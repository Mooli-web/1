# site_settings/apps.py
"""
تنظیمات اپلیکیشن site_settings.
وظیفه اصلی: اطمینان از وجود رکورد تنظیمات هنگام بالا آمدن سرور.
"""

import logging
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db.utils import OperationalError, ProgrammingError

# تنظیم لاگر برای ثبت پیام‌های سیستم
logger = logging.getLogger(__name__)

class SiteSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'site_settings'
    verbose_name = _("تنظیمات سراسری سایت")

    def ready(self):
        """
        بررسی و ایجاد تنظیمات اولیه هنگام راه‌اندازی جنگو.
        """
        try:
            # ایمپورت مدل در داخل متد ready برای جلوگیری از Circular Import
            SiteSettings = self.get_model('SiteSettings')
            
            # تلاش برای بارگذاری یا ایجاد تنظیمات
            SiteSettings.load()
            
        except (OperationalError, ProgrammingError):
            # این خطاها معمولاً زمانی رخ می‌دهند که هنوز مایگریشن‌ها اجرا نشده‌اند
            # یا دیتابیس در دسترس نیست. در این حالت فقط لاگ می‌کنیم و رد می‌شویم.
            # (مثلا موقع اجرای دستور makemigrations)
            logger.info("SiteSettings table not ready yet. Skipping singleton check.")
            
        except Exception as e:
            # خطاهای غیرمنتظره را با سطح Error لاگ می‌کنیم
            logger.error(f"Failed to initialize SiteSettings: {e}")