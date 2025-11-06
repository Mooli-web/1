from .base import *

# --- تنظیمات مخصوص توسعه (Local) ---

# DEBUG در حالت توسعه همیشه روشن است
DEBUG = True

# هاست‌های مجاز برای توسعه
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# استفاده از دیتابیس SQLite برای توسعه آسان
if not DATABASES or 'default' not in DATABASES or not DATABASES['default']:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# نمایش ایمیل‌ها در کنسول به جای ارسال واقعی
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# می‌توانید اپ‌های مخصوص دیباگ را در اینجا اضافه کنید
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']