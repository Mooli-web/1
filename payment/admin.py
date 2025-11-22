# payment/admin.py
"""
تنظیمات پنل ادمین برای مدیریت تراکنش‌ها.
بهینه‌سازی شده برای جلوگیری از فشار روی دیتابیس در لیست‌های طولانی.
"""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from .models import Transaction
from jalali_date.admin import ModelAdminJalaliMixin

@admin.register(Transaction)
class TransactionAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    """
    مدیریت تراکنش‌ها.
    این بخش فقط خواندنی است تا سوابق مالی دستکاری نشوند.
    """
    list_display = (
        'id', 
        'get_patient_name', 
        'amount_display', 
        'status', 
        'created_at_display', 
        'authority'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('appointment__patient__username', 'authority', 'amount')
    raw_id_fields = ('appointment',)
    
    readonly_fields = ('appointment', 'amount', 'status', 'created_at', 'authority')
    list_per_page = 20

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """
        بهینه‌سازی کوئری:
        استفاده از select_related برای دریافت اطلاعات نوبت و بیمار در یک کوئری.
        """
        return super().get_queryset(request).select_related('appointment__patient')

    def get_patient_name(self, obj):
        return obj.appointment.patient.username
    get_patient_name.short_description = "نام کاربر"
    get_patient_name.admin_order_field = 'appointment__patient__username'

    def amount_display(self, obj):
        return f"{obj.amount:,} تومان"
    amount_display.short_description = "مبلغ"
    amount_display.admin_order_field = 'amount'

    def created_at_display(self, obj):
        return obj.created_at
    created_at_display.short_description = "تاریخ ایجاد"

    # --- Permissions: Read-Only ---
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False