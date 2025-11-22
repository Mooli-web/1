# booking/calendar_logic.py
"""
هسته منطقی محاسبات تقویم (Calendar Logic).
وظیفه: تولید اسلات‌های زمانی آزاد با در نظر گرفتن نوبت‌های رزرو شده، ساعات کاری و محدودیت‌ها.
"""

from datetime import datetime, time, timedelta, date
from typing import List, Dict, Union
import jdatetime
from django.utils import timezone
from django.db.models import Q

# --- اصلاحیه ایمپورت‌ها ---
# مدل‌های Service و WorkHours در اپلیکیشن clinic هستند
from clinic.models import Service, WorkHours
# مدل Appointment در همین اپلیکیشن (booking) قرار دارد
from .models import Appointment
from users.models import CustomUser

# --- ثابت‌های فارسی‌سازی ---
PERSIAN_WEEKDAYS = {
    0: "شنبه", 1: "یکشنبه", 2: "دوشنبه", 3: "سه‌شنبه",
    4: "چهارشنبه", 5: "پنجشنبه", 6: "جمعه",
}

PERSIAN_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]

PERSIAN_DIGITS = {
    '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
    '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹',
}

def localize_digits(text: Union[str, int]) -> str:
    """تبدیل اعداد انگلیسی به فارسی."""
    return "".join(PERSIAN_DIGITS.get(char, char) for char in str(text))


def generate_available_slots_for_range(
    start_date: date, 
    end_date: date, 
    service_ids: List[str], 
    device_id: Union[int, None], 
    patient_user: CustomUser
) -> Dict[str, List[Dict]]:
    """
    تولید اسلات‌های خالی برای یک بازه زمانی مشخص.
    """
    
    # 1. اعتبارسنجی اولیه
    try:
        # استفاده از select_related برای کاهش کوئری
        services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not services.exists():
            return {}

        total_duration = sum(s.duration for s in services)
        if total_duration == 0:
            return {}

        service = services.first()
        service_group = service.group

        if service_group.has_devices and not device_id:
            return {}
            
    except Exception:
        return {}

    # 2. فیلتر جنسیت
    user_gender = patient_user.gender
    gender_filter = Q(gender_specific='ALL') 
    if user_gender:
        gender_filter = Q(gender_specific=user_gender) | Q(gender_specific='ALL')
    
    # 3. واکشی ساعات کاری (Work Hours)
    # محاسبه روزهای هفته موجود در بازه زمانی برای کاهش جستجو
    days_diff = (end_date - start_date).days
    weekday_range = set((start_date + timedelta(days=i)).weekday() for i in range(days_diff + 1))
    # تبدیل به فرمت مدل (شنبه=0 در مدل ما) -> در اینجا فرض شده مدل از 0 برای شنبه استفاده میکند
    # اما پایتون دوشنبه را 0 میداند. نیاز به نگاشت:
    # Python: Mon(0), Tue(1), Wed(2), Thu(3), Fri(4), Sat(5), Sun(6)
    # Model (Assumed): Sat(0), Sun(1), Mon(2), ..., Fri(6)
    model_weekdays = [(d + 2) % 7 for d in weekday_range]

    # اولویت با ساعات کاری اختصاصی سرویس است، اگر نبود گروه
    work_hours_qs = service.work_hours.filter(day_of_week__in=model_weekdays).filter(gender_filter)
    if not work_hours_qs.exists():
        work_hours_qs = service.group.work_hours.filter(day_of_week__in=model_weekdays).filter(gender_filter)

    work_hours_map = {}
    for wh in work_hours_qs:
        work_hours_map.setdefault(wh.day_of_week, []).append(wh)

    # 4. واکشی نوبت‌های رزرو شده (Booked Appointments)
    aware_start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    aware_end_dt = timezone.make_aware(datetime.combine(end_date, time.max))

    # فقط نوبت‌های موثر (تایید شده یا در انتظار) را می‌گیریم
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
        # تبدیل به زمان محلی برای مقایسه صحیح روزانه
        local_start = timezone.localtime(app.start_time, current_tz)
        date_key = local_start.date()
        # ذخیره بازه اشغال شده
        booked_intervals_map.setdefault(date_key, set()).add(
            (app.start_time, app.end_time) # زمان‌های Aware نگه داشته می‌شوند
        )

    # 5. تولید اسلات‌ها
    all_available_slots_map = {}
    today = timezone.now().date()
    now = timezone.now()
    
    current_date = start_date
    while current_date <= end_date:
        
        # نوبت‌دهی برای گذشته امکان‌پذیر نیست
        if current_date < today:
            current_date += timedelta(days=1)
            continue

        # نگاشت روز هفته پایتون به مدل
        our_day_of_week = (current_date.weekday() + 2) % 7
        
        daily_work_hours = work_hours_map.get(our_day_of_week, [])
        if not daily_work_hours:
            current_date += timedelta(days=1)
            continue
            
        booked_intervals = booked_intervals_map.get(current_date, set())
        
        for work_period in daily_work_hours:
            # ساخت زمان شروع و پایان شیفت کاری در این تاریخ خاص
            shift_start = timezone.make_aware(datetime.combine(current_date, work_period.start_time))
            shift_end = timezone.make_aware(datetime.combine(current_date, work_period.end_time))
            
            # حلقه تولید اسلات در داخل شیفت
            current_slot_start = shift_start
            
            while True:
                current_slot_end = current_slot_start + timedelta(minutes=total_duration)

                # شرط خروج: اگر پایان اسلات از پایان شیفت بیرون زد
                if current_slot_end > shift_end:
                    break
                
                # شرط اعتبار ۱: اسلات نباید در گذشته باشد (شامل تاریخ امروز و ساعت گذشته)
                if current_slot_end <= now:
                    current_slot_start += timedelta(minutes=total_duration)
                    continue

                # شرط اعتبار ۲: تداخل با نوبت‌های رزرو شده
                is_overlapping = False
                for (b_start, b_end) in booked_intervals:
                    # فرمول استاندارد تداخل دو بازه: (StartA < EndB) and (EndA > StartB)
                    if current_slot_start < b_end and current_slot_end > b_start:
                        is_overlapping = True
                        break
                        
                if not is_overlapping:
                    # اسلات آزاد است -> فرمت‌دهی خروجی
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
                    
                # حرکت به اسلات بعدی
                current_slot_start += timedelta(minutes=total_duration)

        current_date += timedelta(days=1)

    return all_available_slots_map