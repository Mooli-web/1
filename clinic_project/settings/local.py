# clinic_project/settings/local.py
"""
تنظیمات مخصوص محیط "توسعه" (Development / Local).
این فایل base.py را import کرده و تنظیمات آن را برای
محیط توسعه بازنویسی (Override) می‌کند.
"""

from .base import * # وارد کردن تمام تنظیمات پایه

# --- تنظیمات مخصوص توسعه ---

# DEBUG در حالت توسعه همیشه روشن است
DEBUG = True

# هاست‌های مجاز برای توسعه
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# استفاده از دیتابیس SQLite برای توسعه آسان
# (این شرط بررسی می‌کند که آیا دیتابیس در base.py (از .env)
# تنظیم شده است یا خیر. اگر نشده باشد، SQLite را تنظیم می‌کند)
if not DATABASES or 'default' not in DATABASES or not DATABASES['default']:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# نمایش ایمیل‌ها در کنسول به جای ارسال واقعی
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# می‌توانید اپ‌های مخصوص دیباگ (مانند Debug Toolbar) را در اینجا اضافه کنید
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']