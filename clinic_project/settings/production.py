# clinic_project/settings/production.py
"""
تنظیمات مخصوص محیط "محصول نهایی" (Production).
این فایل base.py را import کرده و تنظیمات آن را برای
محیط سرور اصلی بازنویسی (Override) می‌کند.
"""

from .base import * # وارد کردن تمام تنظیمات پایه

# --- تنظیمات مخصوص محصول نهایی ---

# DEBUG در پروداکشن همیشه خاموش است
DEBUG = False

# کلید امنیتی باید "حتما" از متغیرهای محیطی خوانده شود
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# هاست‌های مجاز "حتما" از متغیرهای محیطی خوانده می‌شوند
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(',') if ALLOWED_HOSTS_STRING else []

# دیتابیس در پروداکشن باید "حتما" از DATABASE_URL (متغیر محیطی) تنظیم شود
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL environment variable is not set.")

# --- تنظیمات امنیتی پروداکشن ---
# (این تنظیمات در حال حاضر کامنت هستند، اما برای استقرار نهایی
# بر روی HTTPS باید فعال شوند)

# SECURE_SSL_REDIRECT = True  # هدایت تمام ترافیک HTTP به HTTPS
# SESSION_COOKIE_SECURE = True  # کوکی‌ها فقط روی HTTPS ارسال شوند
# CSRF_COOKIE_SECURE = True  # کوکی CSRF فقط روی HTTPS ارسال شود
# SECURE_HSTS_SECONDS = 31536000  # (1 سال) به مرورگر می‌گوید که همیشه با HTTPS به سایت بیاید
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# (تنظیمات مربوط به فایل‌های استاتیک در Production مانند Whitenoise
# یا S3 نیز باید در این فایل اضافه شوند)