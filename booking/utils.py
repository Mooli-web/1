# booking/utils.py
"""
این فایل شامل توابع کمکی (Helper Functions) برای اپلیکیشن booking است.
هدف این فایل، جدا کردن منطق‌های تکراری و پیچیده از فایل views.py
و افزایش خوانایی ویوها است.
"""

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, time, timedelta
import jdatetime

from users.models import CustomUser
from clinic.models import DiscountCode, Service
from .models import Appointment

# --- Helper 1: تشخیص هویت بیمار ---
def _get_patient_for_booking(request):
    """
    تابع کمکی برای تشخیص اینکه "چه کسی" در حال رزرو نوبت است.
    
    این تابع سه سناریو را مدیریت می‌کند:
    1. بیمار عادی (لاگین کرده و در حال رزرو برای خود است).
    2. پذیرش (در حال رزرو برای یک بیمار خاص است - "act as").
    3. کاربر لاگین نکرده (AnonymousUser).
    
    خروجی: (patient_user, is_reception_booking, patient_user_for_template)
    - patient_user: آبجکت کاربری که نوبت برای او ثبت می‌شود.
    - is_reception_booking: یک بولین (boolean) که مشخص می‌کند آیا پذیرش در حال رزرو است یا خیر.
    - patient_user_for_template: آبجکت بیمار (برای نمایش نام او در تمپلیت).
    """
    is_reception_booking = False
    patient_user = request.user  # پیش‌فرض: کاربری که لاگین کرده
    patient_user_for_template = None

    # سناریوی ۲: پذیرش در حال رزرو برای بیمار است
    if request.user.is_staff and request.session.get('reception_acting_as_patient_id'):
        is_reception_booking = True
        try:
            patient_id = request.session['reception_acting_as_patient_id']
            patient_user = CustomUser.objects.get(id=patient_id)
            patient_user_for_template = patient_user  # برای نمایش در هدر فرم
        except CustomUser.DoesNotExist:
            patient_user = None  # ویو اصلی این None را مدیریت خواهد کرد
    
    # در سناریوی ۱ و ۳، 'patient_user' همان 'request.user' باقی می‌ماند
    return patient_user, is_reception_booking, patient_user_for_template

# --- Helper 2: محاسبه تخفیف‌ها ---
def _calculate_discounts(patient_user, total_price, apply_points_str, discount_code_str):
    """
    تابع کمکی برای محاسبه تخفیف‌های امتیاز (Points) و کد تخفیف (DiscountCode).
    
    خروجی: (points_discount, points_to_use, code_discount, discount_code_obj, error_message)
    """
    points_discount = 0
    points_to_use = 0
    code_discount = 0
    discount_code_obj = None
    error_message = None

    # ۱. محاسبه تخفیف بر اساس امتیازات کاربر
    if apply_points_str:  # اگر چک‌باکس "استفاده از امتیاز" فعال بود
        profile = patient_user.profile
        # حداکثر تخفیفی که بیمار می‌تواند با امتیازش بگیرد
        max_possible_discount = profile.points * settings.POINTS_TO_TOMAN_RATE
        # تخفیف امتیازی نمی‌تواند از قیمت کل بیشتر باشد
        points_discount = min(max_possible_discount, total_price) 
        # محاسبه تعداد امتیازی که باید مصرف شود
        points_to_use = int(points_discount / settings.POINTS_TO_TOMAN_RATE)

    # ۲. محاسبه تخفیف بر اساس کد تخفیف
    if discount_code_str:
        try:
            discount_code_obj = DiscountCode.objects.get(code__iexact=discount_code_str)
            
            # اعتبارسنجی کد
            if not discount_code_obj.is_valid():
                error_message = 'کد تخفیف معتبر نیست یا منقضی شده.'
                discount_code_obj = None
            elif discount_code_obj.user and discount_code_obj.user != patient_user:
                error_message = 'این کد تخفیف مخصوص شما نیست.'
                discount_code_obj = None
            elif discount_code_obj.is_one_time and discount_code_obj.is_used:
                error_message = 'این کد تخفیف قبلاً استفاده شده است.'
                discount_code_obj = None
            else:
                # محاسبه مبلغ تخفیف بر اساس نوع کد
                if discount_code_obj.discount_type == 'PERCENTAGE':
                    code_discount = (total_price * discount_code_obj.value) / 100
                else:  # FIXED_AMOUNT
                    code_discount = discount_code_obj.value
                    
        except DiscountCode.DoesNotExist:
            error_message = 'کد تخفیف یافت نشد.'
            discount_code_obj = None  # اطمینان از اینکه آبجکت کد ارسال نمی‌شود

    return points_discount, points_to_use, code_discount, discount_code_obj, error_message