# booking/utils.py
# فایل جدید: این فایل شامل منطق کمکی و محاسباتی است که از views.py استخراج شده.

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


# ***
# *** تابع کمکی (اصلاح شده) ***
# ***
def get_available_slots_for_day(selected_date, total_duration, service_ids, patient_user, device_id):
    """
    (تابع کمکی) بررسی می‌کند که آیا در یک روز خاص، حداقل یک اسلات خالی وجود دارد یا خیر.
    پارامتر device_id به آن اضافه شده است.
    """
    
    user_gender = patient_user.gender
    if user_gender:
        gender_filter = Q(gender_specific=user_gender) | Q(gender_specific='ALL')
    else:
        gender_filter = Q(gender_specific='ALL')

    try:
        services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not services.exists():
            return 'unavailable' 
        service = services.first()
        service_group = service.group 
        
        # *** بررسی نیاز به دستگاه در تابع کمکی ***
        if service_group.has_devices and not device_id:
            return 'unavailable' # نمی‌توان در دسترس بودن را بدون دستگاه چک کرد

        our_day_of_week = (selected_date.weekday() + 2) % 7 
        
        work_hours_list = service.work_hours.filter(
            day_of_week=our_day_of_week
        ).filter(gender_filter)
        
        if not work_hours_list.exists():
            work_hours_list = service.group.work_hours.filter(
                day_of_week=our_day_of_week
            ).filter(gender_filter)

        if not work_hours_list.exists():
            return 'unavailable' 
            
    except Exception:
        return 'unavailable'

    start_of_day = timezone.make_aware(datetime.combine(selected_date, time.min))
    end_of_day = timezone.make_aware(datetime.combine(selected_date, time.max))
    
    # *** اصلاح کوئری نوبت‌های رزرو شده در تابع کمکی ***
    appointments_query = Appointment.objects.filter(
        start_time__range=(start_of_day, end_of_day),
        status__in=['CONFIRMED', 'PENDING']
    )

    if service_group.has_devices:
        booked_appointments = appointments_query.filter(selected_device_id=device_id)
    else:
        booked_appointments = appointments_query.filter(selected_device__isnull=True)
    
    current_tz = timezone.get_current_timezone()
    booked_intervals = []
    for app in booked_appointments:
        booked_intervals.append(
            (timezone.localtime(app.start_time, current_tz),
             timezone.localtime(app.end_time, current_tz))
        )

    for workday in work_hours_list:
        workday_start, workday_end = workday.start_time, workday.end_time
        current_time_dt = datetime.combine(selected_date, workday_start)
        end_time_dt = datetime.combine(selected_date, workday_end)

        while current_time_dt < end_time_dt:
            potential_start_aware = timezone.make_aware(current_time_dt)
            potential_end_aware = potential_start_aware + timedelta(minutes=total_duration)

            if potential_start_aware > timezone.now(): 
                if potential_end_aware.time() <= workday_end: 
                    is_overlapping = False
                    for start, end in booked_intervals:
                        if (potential_start_aware < end and potential_end_aware > start):
                            is_overlapping = True
                            break
                    
                    if not is_overlapping:
                        return 'available'
            
            if total_duration > 0:
                 current_time_dt += timedelta(minutes=total_duration)
            else:
                 current_time_dt += timedelta(minutes=30)

    return 'full'