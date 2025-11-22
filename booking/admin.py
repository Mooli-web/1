# booking/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن booking.
شامل: مدیریت نوبت‌ها، اکشن‌های سفارشی برای امتیازدهی و پاداش.
"""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from jalali_date.admin import ModelAdminJalaliMixin
from site_settings.models import SiteSettings
from .models import Appointment

# مقدار پاداش اولین مراجعه (بهتر است بعداً به SiteSettings منتقل شود)
WELCOME_BONUS_POINTS = 500 

@admin.action(description="علامت‌گذاری به عنوان 'انجام شده' و اعطای امتیاز")
def mark_as_done_and_award_points(modeladmin, request: HttpRequest, queryset: QuerySet):
    """
    اکشن سفارشی برای:
    1. تغییر وضعیت نوبت به DONE.
    2. محاسبه و اعطای امتیاز (عادی + پاداش خوش‌آمدگویی).
    """
    try:
        # بارگذاری تنظیمات برای نرخ تبدیل پول به امتیاز
        rate = SiteSettings.load().price_to_points_rate
    except Exception:
        rate = 0

    # فیلتر کردن نوبت‌هایی که هنوز امتیاز نگرفته‌اند و تایید شده‌اند
    # استفاده از select_related برای جلوگیری از کوئری‌های اضافی روی بیمار و پروفایل
    valid_appointments = queryset.filter(
        status='CONFIRMED', 
        points_awarded=False
    ).select_related('patient__profile')
    
    count = 0
    for appointment in valid_appointments:
        try:
            # 1. بررسی "اولین" نوبت انجام شده (Cashback Strategy)
            # قبل از اینکه وضعیت این نوبت را DONE کنیم، سوابق قبلی را چک می‌کنیم
            previous_done_count = Appointment.objects.filter(
                patient=appointment.patient, 
                status='DONE'
            ).count()
            
            is_first_visit = (previous_done_count == 0)
            
            # 2. تغییر وضعیت و فلگ امتیاز
            appointment.status = 'DONE'
            appointment.points_awarded = True
            appointment.save(update_fields=['status', 'points_awarded'])
            
            # 3. محاسبه امتیاز
            total_points_to_add = 0
            
            # الف) امتیاز بر اساس تراکنش مالی (اگر وجود داشته باشد)
            # نکته: چون رابطه با transaction احتمالا OneToOne یا FK است، اینجا چک می‌کنیم
            if rate > 0 and hasattr(appointment, 'transaction'):
                txn = appointment.transaction
                if txn.status == 'SUCCESS' and txn.amount > 0:
                    normal_points = int(txn.amount / rate)
                    total_points_to_add += normal_points
            
            # ب) پاداش اولین مراجعه
            if is_first_visit:
                total_points_to_add += WELCOME_BONUS_POINTS
                
            # 4. اعمال امتیاز به پروفایل کاربر
            if total_points_to_add > 0:
                profile = appointment.patient.profile
                profile.points += total_points_to_add
                profile.save(update_fields=['points'])
            
            count += 1
            
        except Exception as e:
            # لاگ کردن خطا بدون متوقف کردن کل پروسه برای سایر آیتم‌ها
            print(f"Error processing appointment {appointment.id}: {e}")

    modeladmin.message_user(request, f"{count} نوبت با موفقیت پردازش شد.")

@admin.register(Appointment)
class AppointmentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        '__str__',
        'patient', 
        'get_services_display', 
        'start_time', 
        'status', 
        'selected_device', 
        'points_awarded'
    )
    list_filter = ('status', 'start_time', 'selected_device', 'points_awarded')
    search_fields = ('patient__username', 'patient__first_name', 'patient__last_name', 'services__name')
    actions = [mark_as_done_and_award_points]
    
    readonly_fields = ('get_services_display', 'created_at')
    list_per_page = 20
    raw_id_fields = ('patient', 'discount_code', 'selected_device')

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """بهینه‌سازی کوئری لیست ادمین"""
        return super().get_queryset(request).select_related(
            'patient', 'selected_device', 'discount_code'
        ).prefetch_related('services')

    def get_services_display(self, obj):
        return obj.get_services_display()
    get_services_display.short_description = "خدمات"