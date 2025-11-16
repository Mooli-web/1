# booking/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن booking.
"""

from django.contrib import admin
from .models import Appointment
from jalali_date.admin import ModelAdminJalaliMixin  # برای نمایش تقویم شمسی
from site_settings.models import SiteSettings  # برای دسترسی به تنظیمات امتیازدهی


# --- تعریف Action سفارشی برای ادمین ---

@admin.action(description="علامت‌گذاری به عنوان 'انجام شده' و اعطای امتیاز")
def mark_as_done_and_award_points(modeladmin, request, queryset):
    """
    یک Action سفارشی در پنل ادمین که:
    1. وضعیت نوبت‌های انتخاب شده را به 'DONE' تغییر می‌دهد.
    2. بر اساس مبلغ پرداخت شده در تراکنش، به بیمار امتیاز می‌دهد.
    """
    try:
        # واکشی تنظیمات نرخ امتیاز از مدل SiteSettings
        rate = SiteSettings.load().price_to_points_rate
    except Exception:
        rate = 0  # اگر تنظیمات موجود نباشد، امتیازی داده نمی‌شود

    # فقط نوبت‌هایی که "تایید شده" هستند و "هنوز امتیاز نگرفته‌اند"
    valid_appointments = queryset.filter(status='CONFIRMED', points_awarded=False)
    
    for appointment in valid_appointments:
        appointment.status = 'DONE'
        appointment.points_awarded = True  # علامت‌گذاری جهت جلوگیری از امتیازدهی مجدد
        appointment.save()
        
        # --- منطق اعطای امتیاز ---
        try:
            # بررسی اینکه آیا نرخ معتبر است و آیا نوبت تراکنش موفق داشته است
            if rate > 0 and hasattr(appointment, 'transaction') and \
               appointment.transaction.status == 'SUCCESS' and \
               appointment.transaction.amount > 0:
                
                # محاسبه امتیاز بر اساس "مبلغ واقعی پرداخت شده"
                points_to_award = int(appointment.transaction.amount / rate)
                
                if points_to_award > 0:
                    appointment.patient.profile.points += points_to_award
                    appointment.patient.profile.save()
                    
        except Exception: 
            # اگر تراکنش وجود نداشته باشد یا خطای دیگری رخ دهد،
            # فقط وضعیت نوبت تغییر می‌کند و امتیازی داده نمی‌شود.
            pass 

# --- ثبت مدل Appointment در ادمین ---

@admin.register(Appointment)
class AppointmentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    """
    کلاس مدیریتی برای نمایش مدل Appointment در پنل ادمین.
    - از ModelAdminJalaliMixin برای تقویم شمسی استفاده می‌کند.
    """
    
    list_display = (
        'patient', 
        'get_services_display',  # متد سفارشی مدل
        'start_time', 
        'status', 
        'selected_device', 
        'points_awarded'  # نمایش وضعیت اعطای امتیاز
    )
    list_filter = ('status', 'start_time', 'selected_device', 'points_awarded')
    search_fields = ('patient__username', 'services__name')
    actions = [mark_as_done_and_award_points]  # افزودن اکشن سفارشی
    
    readonly_fields = ('get_services_display',)
    list_per_page = 20
    
    # استفاده از raw_id_fields برای جستجوی آسان بیمار، کد و دستگاه
    raw_id_fields = ('patient', 'discount_code', 'selected_device')

    def get_services_display(self, obj):
        """
        فراخوانی متد مدل برای نمایش در list_display و readonly_fields.
        """
        return obj.get_services_display()
    get_services_display.short_description = "خدمات"