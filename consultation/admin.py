# consultation/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن consultation.
"""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from .models import ConsultationRequest, ConsultationMessage
from jalali_date.admin import ModelAdminJalaliMixin

class ConsultationMessageInline(admin.TabularInline):
    """
    نمایش پیام‌های چت به صورت ردیفی (Inline).
    """
    model = ConsultationMessage
    extra = 0
    readonly_fields = ('user', 'message', 'timestamp')
    verbose_name = "پیام"
    verbose_name_plural = "پیام‌ها"
    
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    """
    مدیریت درخواست‌های مشاوره.
    """
    list_display = ('subject', 'patient', 'status', 'created_at_display')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'patient__username', 'patient__first_name', 'patient__last_name')
    raw_id_fields = ('patient',)
    inlines = [ConsultationMessageInline]
    list_per_page = 20

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """بهینه‌سازی کوئری برای جلوگیری از N+1"""
        return super().get_queryset(request).select_related('patient')

    def created_at_display(self, obj):
        return obj.created_at
    created_at_display.short_description = "تاریخ ایجاد"