# site_settings/apps.py
"""
تنظیمات اپلیکیشن (AppConfig) برای site_settings.
"""

from django.apps import AppConfig
from django.db.utils import OperationalError
from django.core.exceptions import AppRegistryNotReady

class SiteSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'site_settings'
    verbose_name = "تنظیمات سایت"

    def ready(self):
        """
        این متد زمانی اجرا می‌شود که جنگو آماده راه‌اندازی است.
        وظیفه اصلی آن، اطمینان از "ایجاد شدن" آبجکت Singleton
        تنظیمات (SiteSettings) در دیتابیس در همان ابتدای
        راه‌اندازی سرور است.
        """
        try:
            # Import مدل باید "در داخل" متد ready انجام شود
            SiteSettings = self.get_model('SiteSettings')
            
            # فراخوانی متد load() که get_or_create را اجرا می‌کند
            SiteSettings.load()
            
        except (OperationalError, AppRegistryNotReady) as e:
            # این خطاها در زمان اجرای اولین 'migrate' (زمانی که
            # هنوز جدول site_settings_sitesettings ساخته نشده)
            # کاملاً طبیعی هستند.
            # ما این خطاها را نادیده می‌گیریم تا فرآیند migrate متوقف نشود.
            print(f"Skipping SiteSettings singleton check (normal during migrations): {e}")
        except Exception as e:
            # مدیریت خطاهای پیش‌بینی نشده دیگر
            print(f"Could not load/create SiteSettings singleton: {e}")