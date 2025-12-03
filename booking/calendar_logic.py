# booking/calendar_logic.py
from datetime import datetime, time, timedelta, date
from typing import List, Dict, Union
import jdatetime
from django.utils import timezone
from django.db.models import Q
from clinic.models import Service, WorkHours
from .models import Appointment
from users.models import CustomUser

PERSIAN_WEEKDAYS = {0: "شنبه", 1: "یکشنبه", 2: "دوشنبه", 3: "سه‌شنبه", 4: "چهارشنبه", 5: "پنجشنبه", 6: "جمعه"}
PERSIAN_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
PERSIAN_DIGITS = {'0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴', '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'}

def localize_digits(text: Union[str, int]) -> str:
    return "".join(PERSIAN_DIGITS.get(char, char) for char in str(text))

def generate_available_slots_for_range(
    start_date: date, 
    end_date: date, 
    service_ids: List[str], 
    device_id: Union[int, None], 
    patient_user: Union[CustomUser, None] = None,
    gender_param: str = None
) -> Dict[str, List[Dict]]:
    
    try:
        services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not services.exists(): return {}
        total_duration = sum(s.duration for s in services)
        if total_duration == 0: return {}
        service = services.first()
        service_group = service.group
        if service_group.has_devices and not device_id: return {}
    except Exception:
        return {}

    # --- منطق اصلاح شده جنسیت ---
    target_gender = 'ALL'
    if gender_param in ['MALE', 'FEMALE']:
        target_gender = gender_param
    elif patient_user and patient_user.gender:
        target_gender = patient_user.gender
    else:
        # تغییر مهم: پیش‌فرض برای مهمانان "بانوان" است
        # چون اکثر خدمات کلینیک زیبایی زنانه است.
        target_gender = 'FEMALE' 
        
    gender_filter = Q(gender_specific='ALL') 
    if target_gender != 'ALL':
        gender_filter = Q(gender_specific=target_gender) | Q(gender_specific='ALL')
    
    # --- ادامه کد بدون تغییر ---
    days_diff = (end_date - start_date).days
    weekday_range = set((start_date + timedelta(days=i)).weekday() for i in range(days_diff + 1))
    model_weekdays = [(d + 2) % 7 for d in weekday_range]

    work_hours_qs = service.work_hours.filter(day_of_week__in=model_weekdays).filter(gender_filter)
    if not work_hours_qs.exists():
        work_hours_qs = service.group.work_hours.filter(day_of_week__in=model_weekdays).filter(gender_filter)

    work_hours_map = {}
    for wh in work_hours_qs:
        work_hours_map.setdefault(wh.day_of_week, []).append(wh)

    aware_start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    aware_end_dt = timezone.make_aware(datetime.combine(end_date, time.max))

    booked_qs = Appointment.objects.filter(
        start_time__lt=aware_end_dt,
        end_time__gt=aware_start_dt,
        status__in=['CONFIRMED', 'PENDING']
    )
    
    if service_group.has_devices:
        booked_qs = booked_qs.filter(selected_device_id=device_id)
    else:
        booked_qs = booked_qs.filter(selected_device__isnull=True)
            
    booked_intervals_map = {}
    current_tz = timezone.get_current_timezone()
    
    for app in booked_qs:
        local_start = timezone.localtime(app.start_time, current_tz)
        date_key = local_start.date()
        booked_intervals_map.setdefault(date_key, set()).add((app.start_time, app.end_time))

    all_available_slots_map = {}
    today = timezone.now().date()
    now = timezone.now()
    
    current_date = start_date
    while current_date <= end_date:
        if current_date < today:
            current_date += timedelta(days=1)
            continue

        our_day_of_week = (current_date.weekday() + 2) % 7
        daily_work_hours = work_hours_map.get(our_day_of_week, [])
        if not daily_work_hours:
            current_date += timedelta(days=1)
            continue
            
        booked_intervals = booked_intervals_map.get(current_date, set())
        
        for work_period in daily_work_hours:
            shift_start = timezone.make_aware(datetime.combine(current_date, work_period.start_time))
            shift_end = timezone.make_aware(datetime.combine(current_date, work_period.end_time))
            current_slot_start = shift_start
            
            while True:
                current_slot_end = current_slot_start + timedelta(minutes=total_duration)
                if current_slot_end > shift_end: break
                if current_slot_end <= now:
                    current_slot_start += timedelta(minutes=total_duration)
                    continue

                is_overlapping = False
                for (b_start, b_end) in booked_intervals:
                    if current_slot_start < b_end and current_slot_end > b_start:
                        is_overlapping = True
                        break
                        
                if not is_overlapping:
                    j_start = jdatetime.datetime.fromgregorian(datetime=current_slot_start)
                    readable_string = "{} {} {}، ساعت {}".format(
                        PERSIAN_WEEKDAYS[j_start.weekday()],
                        localize_digits(j_start.day),
                        PERSIAN_MONTHS[j_start.month - 1],
                        localize_digits(j_start.strftime('%H:%M'))
                    )
                    jalali_date_key = j_start.strftime('%Y-%m-%d')
                    
                    slot_data = {
                        "start": current_slot_start.isoformat(),
                        "end": current_slot_end.isoformat(),
                        "readable_start": readable_string
                    }
                    if jalali_date_key not in all_available_slots_map:
                        all_available_slots_map[jalali_date_key] = []
                    all_available_slots_map[jalali_date_key].append(slot_data)
                    
                current_slot_start += timedelta(minutes=total_duration)

        current_date += timedelta(days=1)

    return all_available_slots_map