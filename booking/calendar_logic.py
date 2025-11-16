# booking/calendar_logic.py
"""
این فایل، هسته اصلی و "مغز متفکر" محاسبات تقویم (Calendar Logic) است.

وظیفه اصلی این فایل، تولید لیست دقیق اسلات‌های زمانی در دسترس
بر اساس مجموعه‌ای از قوانین پیچیده شامل:
- ساعات کاری کلینیک (عمومی گروه یا اختصاصی خدمت)
- نوبت‌های قبلی رزرو شده
- دستگاه‌های مورد نیاز
- جنسیت بیمار
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
                                     patient_user: CustomUser) -> list:
    """
    تابع اصلی محاسبه‌گر اسلات‌های خالی.
    
    تمام اسلات‌های خالی موجود در یک بازه زمانی (start_date تا end_date)
    را بر اساس خدمات، دستگاه و جنسیت بیمار محاسبه می‌کند.
    
    خروجی: لیستی از دیکشنری‌ها، هر کدام شامل 'start', 'end' و 'readable_start'
    [{"start": "...", "end": "...", "readable_start": "..."}, ...]
    """
    
    # --- ۱. اعتبارسنجی ورودی و آماده‌سازی ---
    try:
        # واکشی خدمات انتخاب شده و محاسبه مدت زمان کل
        services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not services.exists():
            return []  # اگر خدمتی انتخاب نشده باشد

        total_duration = sum(s.duration for s in services)
        if total_duration == 0:
            return []  # خدمات بدون مدت زمان

        # تمام خدمات باید از یک گروه باشند
        service = services.first()
        service_group = service.group

        # اگر گروه به دستگاه نیاز دارد اما دستگاهی انتخاب نشده، اسلاتی وجود ندارد
        if service_group.has_devices and not device_id:
            return []
            
    except Exception:
        return []  # در صورت خطای ورودی یا عدم وجود سرویس

    # --- ۲. فیلتر جنسیت بر اساس بیمار ---
    user_gender = patient_user.gender
    gender_filter = Q(gender_specific='ALL') # پیش‌فرض
    if user_gender:
        # اگر کاربر جنسیت دارد، ساعت‌های "همه" یا "مخصوص جنسیت او" را نشان بده
        gender_filter = Q(gender_specific=user_gender) | Q(gender_specific='ALL')
    
    # (اگر کاربر جنسیت نداLE، فقط ساعت‌های "همه" نمایش داده می‌شود)

    # --- ۳. بهینه‌سازی: واکشی تمام ساعات کاری و نوبت‌ها (خارج از حلقه) ---

    # ابتدا تمام روزهای هفته در بازه درخواستی را پیدا می‌کنیم (شنبه=۰، ...)
    # (day.weekday() + 2) % 7 فرمول تبدیل شنبه به ۰ است
    weekday_range = list(set([(d.weekday() + 2) % 7 for d in (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1))]))

    # کوئری برای یافتن ساعات کاری مرتبط
    # اولویت با ساعات کاری "اختصاصی خود خدمت"
    work_hours_qs = service.work_hours.filter(
        day_of_week__in=weekday_range
    ).filter(gender_filter)
    
    # اگر خدمت ساعت اختصاصی نداشت، ساعات کاری "گروه" را چک کن
    if not work_hours_qs.exists():
        work_hours_qs = service.group.work_hours.filter(
            day_of_week__in=weekday_range
        ).filter(gender_filter)

    # تبدیل QuerySet به یک دیکشنری (Map) برای دسترسی سریع در حلقه
    # {0: [WorkHours(9-12), WorkHours(14-17)], 1: [...]}
    work_hours_map = {}
    for wh in work_hours_qs:
        work_hours_map.setdefault(wh.day_of_week, []).append(wh)

    # --- واکشی نوبت‌های رزرو شده ---
    
    # ساخت بازه زمانی آگاه (aware) برای کوئری دیتابیس
    aware_start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    aware_end_dt = timezone.make_aware(datetime.combine(end_date, time.max))

    # واکشی *تمام* نوبت‌های رزرو شده (تایید شده یا در انتظار پرداخت)
    booked_appts_query = Appointment.objects.filter(
        start_time__range=(aware_start_dt, aware_end_dt),
        status__in=['CONFIRMED', 'PENDING']
    )
    
    # فیلتر کردن نوبت‌ها بر اساس دستگاه (منطق کلیدی)
    if service_group.has_devices:
        # اگر سرویس ما نیاز به دستگاه دارد، فقط با نوبت‌هایی تداخل دارد
        # که "دقیقا همین دستگاه" را رزرو کرده‌اند.
        booked_appts_query = booked_appts_query.filter(selected_device_id=device_id)
    else:
        # اگر سرویس ما نیاز به دستگاه ندارد، فقط با نوبت‌هایی تداخل دارد
        # که "بدون دستگاه" رزرو شده‌اند.
        booked_appts_query = booked_appts_query.filter(selected_device__isnull=True)
            
    # تبدیل نوبت‌های رزرو شده به یک دیکشنری (Map) برای دسترسی سریع
    # { '2025-11-10': {(aware_start1, aware_end1)}, '2025-11-11': ...}
    booked_intervals_map = {}
    current_tz = timezone.get_current_timezone()
    for app in booked_appts_query:
        local_start = timezone.localtime(app.start_time, current_tz)
        date_key = local_start.date()
        booked_intervals_map.setdefault(date_key, set()).add(
            (local_start, timezone.localtime(app.end_time, current_tz))
        )

    # --- ۴. حلقه اصلی: تولید اسلات‌های خالی ---
    
    all_available_slots = []
    today = timezone.now().date()
    
    current_date = start_date
    while current_date <= end_date:
        
        # از روزهای گذشته عبور کن (مگر اینکه امروز باشد)
        if current_date < today:
            current_date += timedelta(days=1)
            continue

        # روز هفته (شنبه=۰)
        our_day_of_week = (current_date.weekday() + 2) % 7
        
        # ساعات کاری این روز از روی Map
        daily_work_hours = work_hours_map.get(our_day_of_week, [])
        if not daily_work_hours:
            current_date += timedelta(days=1)
            continue # کلینیک در این روز تعطیل است (یا با فیلتر جنسیت، تعطیل است)
            
        # نوبت‌های رزرو شده این روز از روی Map
        booked_intervals = booked_intervals_map.get(current_date, set())
        
        # بررسی هر بازه کاری (مثلاً شیفت صبح، شیفت عصر)
        for work_period in daily_work_hours:
            
            # نقطه شروع اسلات‌ها = شروع بازه کاری
            current_slot_start_dt = datetime.combine(current_date, work_period.start_time)
            # نقطه پایان بازه کاری
            work_period_end_dt = datetime.combine(current_date, work_period.end_time)
            
            current_slot_start_aware = timezone.make_aware(current_slot_start_dt)
            
            # شروع تولید اسلات‌ها در این بازه کاری (مثلاً شیفت صبح)
            while True:
                # محاسبه زمان پایان اسلات بالقوه
                potential_end_aware = current_slot_start_aware + timedelta(minutes=total_duration)

                # شرط ۱: اگر اسلات در گذشته است، برو سراغ بعدی
                # (این شرط برای اسلات‌های "امروز" مهم است)
                if potential_end_aware <= timezone.now():
                    current_slot_start_aware += timedelta(minutes=total_duration)
                    continue
                
                # شرط ۲: اگر انتهای اسلات از انتهای بازه کاری رد شد، این بازه تمام است
                if potential_end_aware.time() > work_period.end_time:
                    break
                    
                # شرط ۳: بررسی تداخل با نوبت‌های رزرو شده
                is_overlapping = False
                for (booked_start, booked_end) in booked_intervals:
                    # (StartA < EndB) and (EndA > StartB)
                    if (current_slot_start_aware < booked_end and potential_end_aware > booked_start):
                        is_overlapping = True
                        break  # این اسلات تداخل دارد، از حلقه تداخل خارج شو
                        
                if not is_overlapping:
                    # --- *** شروع اصلاحیه: ساخت رشته کاملاً فارسی در پایتون *** ---
                    aware_start_dt = current_slot_start_aware
                    
                    # تبدیل به زمان شمسی
                    j_start = jdatetime.datetime.fromgregorian(datetime=aware_start_dt)
                    
                    # استخراج نام روز هفته (شنبه=0)
                    weekday_name = PERSIAN_WEEKDAYS[j_start.weekday()]
                    
                    # استخراج نام ماه (ماه 1-based است، ایندکس 0-based)
                    month_name = PERSIAN_MONTHS[j_start.month - 1]
                    
                    # تبدیل روز و ساعت به فارسی
                    day_farsi = localize_digits(j_start.day)
                    time_farsi = localize_digits(j_start.strftime('%H:%M'))
                    
                    # ساخت رشته نهایی
                    readable_string = f"{weekday_name} {day_farsi} {month_name}، ساعت {time_farsi}"
                    # --- *** پایان اصلاحیه *** ---

                    # این یک اسلات خالی و معتبر است
                    all_available_slots.append({
                        "start": aware_start_dt.isoformat(),
                        "end": potential_end_aware.isoformat(),
                        "readable_start": readable_string  # <-- کلید حاوی رشته فارسی آماده
                    })
                    
                # به اندازه مدت زمان سرویس به جلو برو تا اسلات بعدی را چک کنی
                current_slot_start_aware += timedelta(minutes=total_duration)

        # برو به روز بعد
        current_date += timedelta(days=1)

    return all_available_slots