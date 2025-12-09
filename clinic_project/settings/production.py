# clinic_project/settings/production.py
"""
تنظیمات محیط "عملیاتی" (Production).
این تنظیمات برای امنیت و کارایی روی سرور واقعی بهینه شده‌اند.
"""

import os
from .base import *

# --- Critical Settings ---
DEBUG = False

# کلید امنیتی باید حتماً ست شده باشد
if not SECRET_KEY or SECRET_KEY == 'django-insecure-dev-key-change-me-in-prod':
    raise ValueError("SECRET_KEY must be set in environment variables for production!")

if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must be set in environment variables for production!")

# دیتابیس باید حتماً ست شده باشد
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in environment variables for production!")


# --- Security Enhancements (HTTPS) ---
# هشدار: این تنظیمات را فقط زمانی فعال کنید که SSL/HTTPS روی سرور فعال باشد.
# در غیر این صورت ممکن است دسترسی به سایت قطع شود.

SECURE_SSL_REDIRECT = True         # هدایت تمام درخواست‌ها به HTTPS
SESSION_COOKIE_SECURE = True       # کوکی نشست فقط در HTTPS
CSRF_COOKIE_SECURE = True          # کوکی CSRF فقط در HTTPS
SECURE_HSTS_SECONDS = 31536000     # اجبار مرورگر به استفاده از HTTPS (یک سال)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


# --- Static Files in Production ---
# برای سرو کردن فایل‌های استاتیک در پروداکشن، معمولاً از WhiteNoise یا Nginx استفاده می‌شود.
# اگر از WhiteNoise استفاده می‌کنید:
# INSTALLED_APPS.append('whitenoise.runserver_nostatic')
# MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'