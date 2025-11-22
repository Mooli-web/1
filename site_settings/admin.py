# site_settings/admin.py
"""
تنظیمات پنل ادمین برای مدل‌های اپلیکیشن site_settings.
"""

from django.contrib import admin
from django.http import HttpRequest
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """
    مدیریت تنظیمات سایت.
    طوری پیکربندی شده که رفتار Singleton داشته باشد (بدون دکمه افزودن یا حذف).
    """
    list_display = ('__str__', 'price_to_points_rate')
    
    # --- مدیریت Singleton ---
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        جلوگیری از ایجاد نمونه جدید.
        اگر به هر دلیلی نمونه وجود نداشت (که نباید پیش بیاید)، اجازه ساخت نمی‌دهد
        چون apps.py وظیفه ساخت آن را دارد.
        """
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        """
        جلوگیری از حذف تنظیمات.
        """
        return False

    def changelist_view(self, request: HttpRequest, extra_context=None):
        """
        (اختیاری) می‌توان کاربر را مستقیماً به صفحه ویرایش ریدایرکت کرد،
        اما نمایش لیست هم مشکلی ندارد.
        """
        return super().changelist_view(request, extra_context)