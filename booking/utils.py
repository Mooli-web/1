# booking/utils.py
from django.conf import settings
from typing import Tuple, Optional, Any
from users.models import CustomUser
from clinic.models import DiscountCode
from site_settings.models import SiteSettings

def _get_patient_for_booking(request) -> Tuple[Optional[CustomUser], bool, Optional[CustomUser]]:
    """
    تشخیص هویت بیمار (خود کاربر یا رزرو توسط پذیرش).
    """
    is_reception_booking = False
    patient_user = request.user
    patient_user_for_template = None

    if request.user.is_staff and request.session.get('reception_acting_as_patient_id'):
        is_reception_booking = True
        try:
            p_id = request.session['reception_acting_as_patient_id']
            patient_user = CustomUser.objects.get(id=p_id)
            patient_user_for_template = patient_user
        except CustomUser.DoesNotExist:
            patient_user = None 
    
    return patient_user, is_reception_booking, patient_user_for_template

def _calculate_discounts(patient_user: CustomUser, total_price: float, apply_points: bool, discount_code_str: str):
    """
    محاسبه تخفیف‌های امتیازی و کدی.
    """
    points_discount = 0
    points_to_use = 0
    code_discount = 0
    discount_obj = None
    error_msg = None

    # 1. امتیاز
    if apply_points:
        try:
            # بارگذاری نرخ تبدیل از تنظیمات (با مقدار پیش‌فرض امن)
            rate = SiteSettings.load().price_to_points_rate
            points_value_toman = settings.POINTS_TO_TOMAN_RATE # یا از تنظیمات
        except:
            points_value_toman = 100 # Default fallback

        profile = patient_user.profile
        max_discount = profile.points * points_value_toman
        points_discount = min(max_discount, total_price)
        if points_value_toman > 0:
            points_to_use = int(points_discount / points_value_toman)

    # 2. کد تخفیف
    if discount_code_str:
        try:
            discount_obj = DiscountCode.objects.get(code__iexact=discount_code_str)
            if not discount_obj.is_valid():
                error_msg = 'کد تخفیف معتبر نیست.'
                discount_obj = None
            elif discount_obj.user and discount_obj.user != patient_user:
                error_msg = 'کد تخفیف متعلق به شما نیست.'
                discount_obj = None
            elif discount_obj.is_one_time and discount_obj.is_used:
                error_msg = 'کد قبلا استفاده شده.'
                discount_obj = None
            else:
                if discount_obj.discount_type == 'PERCENTAGE':
                    code_discount = (total_price * discount_obj.value) / 100
                else:
                    code_discount = discount_obj.value
        except DiscountCode.DoesNotExist:
            error_msg = 'کد تخفیف یافت نشد.'
            discount_obj = None

    return points_discount, points_to_use, code_discount, discount_obj, error_msg