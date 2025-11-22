# reception_panel/admin.py
"""
تنظیمات پنل ادمین برای اپلیکیشن reception_panel.
"""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from .models import Notification
from jalali_date.admin import ModelAdminJalaliMixin

@admin.register(Notification)
class NotificationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    """
    مدیریت اعلان‌ها در پنل ادمین.
    """
    list_display = ('user', 'message', 'is_read', 'created_at_display', 'link')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'message')
    raw_id_fields = ('user',)
    list_editable = ('is_read',)
    list_per_page = 50

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """بهینه‌سازی کوئری"""
        return super().get_queryset(request).select_related('user')

    def created_at_display(self, obj):
        return obj.created_at
    created_at_display.short_description = "تاریخ ایجاد"