# booking/calendar_logic.py
# فایل اصلاح‌شده: خطای ایمپورت Appointment برطرف شد.

from django.utils import timezone
from django.db.models import Q
from datetime import datetime, time, timedelta

# --- این بخش اصلاح شد ---
from clinic.models import Service, WorkHours
# مدل Appointment از clinic.models وارد نمی‌شد، بلکه باید از .models (همین پوشه) وارد شود
from .models import Appointment
# --- پایان اصلاح ---

from users.models import CustomUser

def generate_available_slots_for_range(start_date: datetime.date, 
                                     end_date: datetime.date, 
                                     service_ids: list, 
                                     device_id: int, 
                                     patient_user: CustomUser) -> list:
    """
    هسته اصلی محاسبات تقوim.
    تمام اسلات‌های خالی موجود در یک بازه زمانی (start_date تا end_date)
    را بر اساس خدمات، دستگاه و جنسیت بیمار محاسبه می‌کند.
    """
    
    # --- ۱. اعتبارسنجی ورودی و آماده‌سازی ---
    try:
        services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not services.exists():
            return []  # اگر خدمتی انتخاب نشده باشد، هیچ اسلاتی وجود ندارد

        total_duration = sum(s.duration for s in services)
        if total_duration == 0:
            return []  # اگر خدمات مدت زمان صفر داشته باشند

        service = services.first()
        service_group = service.group

        # اگر گروه به دستگاه نیاز دارد اما دستگاهی انتخاب نشده، اسلاتی وجود ندارد
        if service_group.has_devices and not device_id:
            return []
            
    except Exception:
        return [] # در صورت خطای ورودی

    # --- ۲. فیلتر جنسیت بر اساس بیمار ---
    user_gender = patient_user.gender
    if user_gender:
        gender_filter = Q(gender_specific=user_gender) | Q(gender_specific='ALL')
    else:
        # اگر کاربر جنسیتی انتخاب نکرده، فقط ساعت‌های "همه" را نشان بده
        gender_filter = Q(gender_specific='ALL')

    # --- ۳. بهینه‌سازی: واکشی تمام ساعات کاری و نوبت‌ها (خارج از حلقه) ---

    # روزهای هفته در بازه زمانی (شنبه=۰، یکشنبه=۱ ...)
    # (day.weekday() + 2) % 7
    weekday_range = list(set([(d.weekday() + 2) % 7 for d in (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1))]))

    # ابتدا ساعات کاری مخصوص خود خدمت را پیدا کن
    work_hours_qs = service.work_hours.filter(
        day_of_week__in=weekday_range
    ).filter(gender_filter)
    
    # اگر ساعت مخصوص نداشت، ساعات کاری گروه را چک کن
    if not work_hours_qs.exists():
        work_hours_qs = service.group.work_hours.filter(
            day_of_week__in=weekday_range
        ).filter(gender_filter)

    # تبدیل QuerySet به یک دیکشنری برای دسترسی سریع (Map)
    # {0: [WorkHours(9-12), WorkHours(14-17)], 1: [...]}
    work_hours_map = {}
    for wh in work_hours_qs:
        work_hours_map.setdefault(wh.day_of_week, []).append(wh)

    # واکشی *تمام* نوبت‌های رزرو شده در بازه زمانی درخواستی
    aware_start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    aware_end_dt = timezone.make_aware(datetime.combine(end_date, time.max))

    # اینجا دیگر خطا نمی‌دهد، چون Appointment به درستی ایمپورت شده است
    booked_appts_query = Appointment.objects.filter(
        start_time__range=(aware_start_dt, aware_end_dt),
        status__in=['CONFIRMED', 'PENDING']
    )
    
    # فیلتر کردن نوبت‌ها بر اساس دستگاه (منطق کلیدی)
    if service_group.has_devices:
        booked_appts_query = booked_appts_query.filter(selected_device_id=device_id)
    else:
        booked_appts_query = booked_appts_query.filter(selected_device__isnull=True)
            
    # تبدیل نوبت‌های رزرو شده به یک دیکشنری برای دسترسی سریع
    # { '2025-11-10': {(aware_start, aware_end)}, '2025-11-11': ...}
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
        
        # از روزهای گذشته عبور کن
        if current_date < today:
            current_date += timedelta(days=1)
            continue

        # روز هفته (شنبه=۰)
        our_day_of_week = (current_date.weekday() + 2) % 7
        
        # ساعات کاری این روز
        daily_work_hours = work_hours_map.get(our_day_of_week, [])
        if not daily_work_hours:
            current_date += timedelta(days=1)
            continue # کلینیک در این روز تعطیل است
            
        # نوبت‌های رزرو شده این روز
        booked_intervals = booked_intervals_map.get(current_date, set())
        
        # بررسی هر بازه کاری (مثلاً شیفت صبح، شیفت عصر)
        for work_period in daily_work_hours:
            
            current_slot_start_dt = datetime.combine(current_date, work_period.start_time)
            work_period_end_dt = datetime.combine(current_date, work_period.end_time)
            
            current_slot_start_aware = timezone.make_aware(current_slot_start_dt)
            
            # شروع تولید اسلات‌ها در این بازه کاری
            while True:
                potential_end_aware = current_slot_start_aware + timedelta(minutes=total_duration)

                # ۱. اگر اسلات در گذشته است، برو سراغ بعدی
                if potential_end_aware <= timezone.now():
                    current_slot_start_aware += timedelta(minutes=total_duration)
                    continue
                
                # ۲. اگر انتهای اسلات از انتهای بازه کاری رد شد، این بازه تمام است
                if potential_end_aware.time() > work_period.end_time:
                    break
                    
                # ۳. بررسی تداخل با نوبت‌های رزرو شده
                is_overlapping = False
                for (booked_start, booked_end) in booked_intervals:
                    # (StartA < EndB) and (EndA > StartB)
                    if (current_slot_start_aware < booked_end and potential_end_aware > booked_start):
                        is_overlapping = True
                        break
                        
                if not is_overlapping:
                    # این یک اسلات خالی و معتبر است
                    all_available_slots.append({
                        "start": current_slot_start_aware.isoformat(),
                        "end": potential_end_aware.isoformat()
                    })
                    
                # به اندازه مدت زمان سرویس به جلو برو
                current_slot_start_aware += timedelta(minutes=total_duration)

        # برو به روز بعد
        current_date += timedelta(days=1)

    return all_available_slots