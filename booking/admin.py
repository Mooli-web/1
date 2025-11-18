# booking/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن booking.
اصلاح شده: افزودن منطق 'پاداش اولین مراجعه' (Welcome Bonus) در هنگام تکمیل نوبت.
"""

from django.contrib import admin
from .models import Appointment
from jalali_date.admin import ModelAdminJalaliMixin
from site_settings.models import SiteSettings
from django.conf import settings  # برای دسترسی به تنظیمات پروژه

# --- تعریف ثابت پاداش (می‌تواند به SiteSettings منتقل شود) ---
# فرض: هر امتیاز = 100 تومان (طبق settings.py)
# هدف: 50,000 تومان پاداش
# پس: 50000 / 100 = 500 امتیاز
WELCOME_BONUS_POINTS = 500 


@admin.action(description="علامت‌گذاری به عنوان 'انجام شده' و اعطای امتیاز")
def mark_as_done_and_award_points(modeladmin, request, queryset):
    """
    اکشن سفارشی:
    1. وضعیت را به DONE تغییر می‌دهد.
    2. امتیاز تراکنش را محاسبه می‌کند.
    3. چک می‌کند اگر اولین مراجعه باشد، پاداش خوش‌آمدگویی (Cashback) می‌دهد.
    """
    try:
        rate = SiteSettings.load().price_to_points_rate
    except Exception:
        rate = 0

    # فقط نوبت‌های تایید شده که هنوز امتیاز نگرفته‌اند
    valid_appointments = queryset.filter(status='CONFIRMED', points_awarded=False)
    
    for appointment in valid_appointments:
        
        # 1. بررسی اینکه آیا این "اولین" نوبت انجام شده کاربر است؟
        # (قبل از اینکه وضعیت این نوبت را DONE کنیم چک می‌کنیم)
        previous_done_count = Appointment.objects.filter(
            patient=appointment.patient, 
            status='DONE'
        ).count()
        
        is_first_visit = (previous_done_count == 0)
        
        # 2. تغییر وضعیت
        appointment.status = 'DONE'
        appointment.points_awarded = True
        appointment.save()
        
        # 3. محاسبه و اعطای امتیاز
        try:
            total_points_to_add = 0
            
            # الف) امتیاز عادی (بر اساس مبلغ پرداخت شده)
            if rate > 0 and hasattr(appointment, 'transaction') and \
               appointment.transaction.status == 'SUCCESS' and \
               appointment.transaction.amount > 0:
                normal_points = int(appointment.transaction.amount / rate)
                total_points_to_add += normal_points
            
            # ب) پاداش اولین مراجعه (Cashback Strategy)
            if is_first_visit:
                total_points_to_add += WELCOME_BONUS_POINTS
                # (اختیاری: می‌توان اینجا لاگ یا پیامی برای ادمین چاپ کرد)
                
            # ذخیره امتیاز در پروفایل
            if total_points_to_add > 0:
                appointment.patient.profile.points += total_points_to_add
                appointment.patient.profile.save()
                    
        except Exception as e:
            print(f"Error awarding points for appointment {appointment.id}: {e}")

@admin.register(Appointment)
class AppointmentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'patient', 
        'get_services_display', 
        'start_time', 
        'status', 
        'selected_device', 
        'points_awarded'
    )
    list_filter = ('status', 'start_time', 'selected_device', 'points_awarded')
    search_fields = ('patient__username', 'services__name')
    actions = [mark_as_done_and_award_points]
    
    readonly_fields = ('get_services_display',)
    list_per_page = 20
    raw_id_fields = ('patient', 'discount_code', 'selected_device')

    def get_services_display(self, obj):
        return obj.get_services_display()
    get_services_display.short_description = "خدمات"