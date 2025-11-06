from .base import *

# --- تنظیمات مخصوص محصول نهایی (Production) ---

# DEBUG در پروداکشن همیشه خاموش است
DEBUG = False

# کلید امنیتی باید حتما از متغیرهای محیطی خوانده شود
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# هاست‌های مجاز از متغیرهای محیطی خوانده می‌شوند
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(',') if ALLOWED_HOSTS_STRING else []

# دیتابیس در پروداکشن باید حتما از DATABASE_URL تنظیم شود
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL environment variable is not set.")

# تنظیمات امنیتی پروداکشن (در صورت نیاز فعال شوند)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True