# booking/calendar_logic.py
"""
این فایل، هسته اصلی و "مغز متفکر" محاسبات تقویم (Calendar Logic) است.

وظیفه اصلی این فایل، تولید لیست دقیق اسلات‌های زمانی در دسترس
بر اساس مجموعه‌ای از قوانین پیچیده شامل:
- ساعات کاری کلینیک (عمومی گروه یا اختصاصی خدمت)
- نوبت‌های قبلی رزرو شده
- دستگاه‌های مورد نیاز
- جنسیت بیمار

--- نسخه v2.0 (Smart Backend Refactor) ---
- خروجی تابع به یک دیکشنری (map) تبدیل شده است.
- کلیدهای این دیکشنری، تاریخ شمسی (مانند '1404-08-26') هستند.
- این کار تمام منطق پردازش و گروه‌بندی تاریخ را از JS حذف می‌کند.
"""

from django.utils import timezone
from django.db.models import Q
from datetime import datetime, time, timedelta
import jdatetime  # <-- ایمپورت کتابخانه جلالی

# ایمپورت‌های ضروری از اپ‌های دیگر
from clinic.models import Service, WorkHours
from .models import Appointment  # مدل Appointment از همین اپ (booking)
from users.models import CustomUser

# --- *** شروع اصلاحیه: تعریف دیکشنری‌های فارسی *** ---

# دیکشنری روزهای هفته (شنبه = 0)
PERSIAN_WEEKDAYS = {
    0: "شنبه",
    1: "یکشنبه",
    2: "دوشنبه",
    3: "سه‌شنبه",
    4: "چهارشنبه",
    5: "پنجشنبه",
    6: "جمعه",
}

# لیست ماه‌های شمسی (فروردین = ایندکس 0)
PERSIAN_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]

# دیکشنری تبدیل اعداد
PERSIAN_DIGITS = {
    '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
    '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹',
}

def localize_digits(text):
    """یک رشته (مانند '16:00' یا '25') را می‌گیرد و اعداد آن را فارسی می‌کند."""
    return "".join(PERSIAN_DIGITS.get(char, char) for char in str(text))

# --- *** پایان اصلاحیه *** ---


def generate_available_slots_for_range(start_date: datetime.date, 
                                     end_date: datetime.date, 
                                     service_ids: list, 
                                     device_id: int, 
                                     patient_user: CustomUser) -> dict: # <-- *** تغییر نوع خروجی به dict ***
    """
    تابع اصلی محاسبه‌گر اسلات‌های خالی.
    
    خروجی: دیکشنری گروه‌بندی شده بر اساس تاریخ شمسی
    {"1404-08-26": [{"start": ..., "end": ..., "readable_start": ...}, ...], ...}
    """
    
    # --- ۱. اعتبارسازی ورودی و آماده‌سازی ---
    try:
        services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not services.exists():
            return {}  # <-- خروجی دیکشنری خالی

        total_duration = sum(s.duration for s in services)
        if total_duration == 0:
            return {}  # <-- خروجی دیکشنری خالی

        service = services.first()
        service_group = service.group

        if service_group.has_devices and not device_id:
            return {}
            
    except Exception:
        return {}  # <-- خروجی دیکشنری خالی

    # --- ۲. فیلتر جنسیت بر اساس بیمار ---
    user_gender = patient_user.gender
    gender_filter = Q(gender_specific='ALL') 
    if user_gender:
        gender_filter = Q(gender_specific=user_gender) | Q(gender_specific='ALL')
    
    # --- ۳. بهینه‌سازی: واکشی تمام ساعات کاری و نوبت‌ها (خارج از حلقه) ---
    weekday_range = list(set([(d.weekday() + 2) % 7 for d in (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1))]))

    work_hours_qs = service.work_hours.filter(
        day_of_week__in=weekday_range
    ).filter(gender_filter)
    
    if not work_hours_qs.exists():
        work_hours_qs = service.group.work_hours.filter(
            day_of_week__in=weekday_range
        ).filter(gender_filter)

    work_hours_map = {}
    for wh in work_hours_qs:
        work_hours_map.setdefault(wh.day_of_week, []).append(wh)

    # --- واکشی نوبت‌های رزرو شده ---
    aware_start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    aware_end_dt = timezone.make_aware(datetime.combine(end_date, time.max))

    booked_appts_query = Appointment.objects.filter(
        start_time__range=(aware_start_dt, aware_end_dt),
        status__in=['CONFIRMED', 'PENDING']
    )
    
    if service_group.has_devices:
        booked_appts_query = booked_appts_query.filter(selected_device_id=device_id)
    else:
        booked_appts_query = booked_appts_query.filter(selected_device__isnull=True)
            
    booked_intervals_map = {}
    current_tz = timezone.get_current_timezone()
    for app in booked_appts_query:
        local_start = timezone.localtime(app.start_time, current_tz)
        date_key = local_start.date()
        booked_intervals_map.setdefault(date_key, set()).add(
            (local_start, timezone.localtime(app.end_time, current_tz))
        )

    # --- ۴. حلقه اصلی: تولید اسلات‌های خالی ---
    
    # ====================================================================
    # --- *** شروع تغییر اصلی (فاز ۱) *** ---
    #
    # به جای لیست، از دیکشنری (Map) استفاده می‌کنیم.
    all_available_slots_map = {}
    #
    # --- *** پایان تغییر اصلی (فاز ۱) *** ---
    # ====================================================================

    today = timezone.now().date()
    
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
            
            current_slot_start_dt = datetime.combine(current_date, work_period.start_time)
            work_period_end_dt = datetime.combine(current_date, work_period.end_time)
            current_slot_start_aware = timezone.make_aware(current_slot_start_dt)
            
            while True:
                potential_end_aware = current_slot_start_aware + timedelta(minutes=total_duration)

                # ==========================================================
                # --- *** شروع اصلاحیه (حل مشکلات ۳ و ۴) *** ---
                #
                # بررسی می‌کنیم که *زمان شروع* اسلات در گذشته نباشد
                if current_slot_start_aware <= timezone.now():
                # --- *** پایان اصلاحیه *** ---
                # ==========================================================
                    current_slot_start_aware += timedelta(minutes=total_duration)
                    continue
                
                if potential_end_aware.time() > work_period.end_time:
                    break
                    
                is_overlapping = False
                for (booked_start, booked_end) in booked_intervals:
                    if (current_slot_start_aware < booked_end and potential_end_aware > booked_start):
                        is_overlapping = True
                        break
                        
                if not is_overlapping:
                    # --- این اسلات خالی و معتبر است ---
                    
                    aware_start_dt = current_slot_start_aware
                    
                    # --- ۱. ساخت آبجکت شمسی ---
                    j_start = jdatetime.datetime.fromgregorian(datetime=aware_start_dt)
                    
                    # --- ۲. ساخت رشته فارسی (برای نمایش به کاربر) ---
                    weekday_name = PERSIAN_WEEKDAYS[j_start.weekday()]
                    month_name = PERSIAN_MONTHS[j_start.month - 1]
                    day_farsi = localize_digits(j_start.day)
                    time_farsi = localize_digits(j_start.strftime('%H:%M'))
                    readable_string = f"{weekday_name} {day_farsi} {month_name}، ساعت {time_farsi}"
                    
                    # ====================================================================
                    # --- *** شروع تغییر اصلی (فاز ۱) *** ---
                    #
                    # --- ۳. ساخت کلید شمسی (برای جاوا اسکریپت) ---
                    #    (خروجی: '1404-08-26')
                    jalali_date_key = j_start.strftime('%Y-%m-%d')

                    # ۴. ساخت دیکشنری داده اسلات
                    slot_data = {
                        "start": aware_start_dt.isoformat(),
                        "end": potential_end_aware.isoformat(),
                        "readable_start": readable_string
                    }
                    
                    # ۵. افزودن اسلات به دیکشنری اصلی با استفاده از کلید شمسی
                    if jalali_date_key not in all_available_slots_map:
                        all_available_slots_map[jalali_date_key] = []
                    
                    all_available_slots_map[jalali_date_key].append(slot_data)
                    #
                    # --- *** پایان تغییر اصلی (فاز ۱) *** ---
                    # ====================================================================
                    
                current_slot_start_aware += timedelta(minutes=total_duration)

        current_date += timedelta(days=1)

    # بازگرداندن دیکشنری گروه‌بندی شده
    return all_available_slots_map