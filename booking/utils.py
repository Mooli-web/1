# booking/utils.py
# فایل اصلاح‌شده: تابع محاسباتی تقوim از این فایل حذف شده و به calendar_logic.py منتقل می‌شود.

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, time, timedelta
import jdatetime

from users.models import CustomUser
from clinic.models import DiscountCode, Service
from .models import Appointment

# --- REFACTOR HELPER 1: Get Patient User ---
def _get_patient_for_booking(request):
    """
    Determines which patient is booking.
    Returns (patient_user, is_reception_booking, patient_user_for_template)
    """
    is_reception_booking = False
    patient_user = request.user
    patient_user_for_template = None

    if request.user.is_staff and request.session.get('reception_acting_as_patient_id'):
        is_reception_booking = True
        try:
            patient_user = CustomUser.objects.get(id=request.session['reception_acting_as_patient_id'])
            patient_user_for_template = patient_user # For template context
        except CustomUser.DoesNotExist:
            patient_user = None # Will be caught later
    
    return patient_user, is_reception_booking, patient_user_for_template

# --- REFACTOR HELPER 2: Calculate Discounts ---
def _calculate_discounts(patient_user, total_price, apply_points_str, discount_code_str):
    """
    Calculates points and code discounts.
    Returns (points_discount, points_to_use, code_discount, discount_code_obj, error_message)
    """
    points_discount = 0
    points_to_use = 0
    code_discount = 0
    discount_code_obj = None
    error_message = None

    # 1. Calculate points discount
    if apply_points_str:
        profile = patient_user.profile
        max_possible_discount = profile.points * settings.POINTS_TO_TOMAN_RATE
        points_discount = min(max_possible_discount, total_price) 
        points_to_use = int(points_discount / settings.POINTS_TO_TOMAN_RATE)

    # 2. Calculate code discount
    if discount_code_str:
        try:
            discount_code_obj = DiscountCode.objects.get(code__iexact=discount_code_str)
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
                if discount_code_obj.discount_type == 'PERCENTAGE':
                    code_discount = (total_price * discount_code_obj.value) / 100
                else: # FIXED_AMOUNT
                    code_discount = discount_code_obj.value
        except DiscountCode.DoesNotExist:
            error_message = 'کد تخفیف یافت نشد.'
            discount_code_obj = None # Ensure it's None

    return points_discount, points_to_use, code_discount, discount_code_obj, error_message

