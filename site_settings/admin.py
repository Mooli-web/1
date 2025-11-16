# site_settings/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن site_settings.
"""

from django.contrib import admin
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """
    کلاس مدیریتی برای "تنظیمات سایت".
    این کلاس از ایجاد یا حذف آبجکت‌های اضافی جلوگیری می‌کند.
    """
    list_display = ('price_to_points_rate',)
    
    # --- مدیریت Singleton ---
    
    def has_add_permission(self, request):
        """
        جلوگیری از ایجاد نمونه جدید (چون Singleton است).
        ادمین فقط می‌تواند نمونه موجود (pk=1) را "ویرایش" کند.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        جلوگیری از حذف نمونه Singleton.
        """
        return False