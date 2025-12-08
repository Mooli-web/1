# clinic_project/settings/local.py
"""
تنظیمات محیط "توسعه" (Local Development).
این فایل برای اجرا روی سیستم شخصی برنامه‌نویس است و نباید در سرور اصلی استفاده شود.
"""

from .base import *

# --- Debug Mode ---
# در محیط لوکال همیشه روشن باشد تا خطاها را کامل ببینیم
DEBUG = True

# --- Allowed Hosts ---
ALLOWED_HOSTS = ['*']

# --- Database ---
# اگر دیتابیس اصلی (PostgreSQL) در .env تنظیم نشده بود، از SQLite استفاده کن
if not DATABASES or 'default' not in DATABASES or not DATABASES['default']:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- Email ---
# چاپ ایمیل‌ها در کنسول به جای ارسال واقعی
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# --- Debug Toolbar (Optional) ---
# اگر نیاز به دیباگ تولبار داشتید، اینجا اضافه کنید
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']