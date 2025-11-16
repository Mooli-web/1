# clinic_project/settings/base.py
"""
تنظیمات "پایه" (Base) پروژه جنگو.
این تنظیمات در هر دو محیط "توسعه" (local) و "محصول نهایی" (production)
مشترک هستند.
فایل‌های local.py و production.py این فایل را import کرده
و تنظیمات آن را بازنویسی (Override) می‌کنند.
"""

import os
from pathlib import Path
import dj_database_url  # برای خواندن DATABASE_URL از متغیرهای محیطی
from datetime import timedelta

# تعریف مسیر پایه پروژه (BASE_DIR)
# (settings -> clinic_project -> mooli-web)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# بارگذاری متغیرهای محیطی از فایل .env (اگر وجود داشته باشد)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    pass

# --- تنظیمات کلیدی ---

# کلید امنیتی (باید در production از .env خوانده شود)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-default-key-for-dev')

# هاست‌های مجاز (باید در production از .env خوانده شود)
ALLOWED_HOSTS_STRING = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(',') if ALLOWED_HOSTS_STRING else []

# وضعیت DEBUG (در local.py و production.py بازنویسی می‌شود)
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'


# --- اپلیکیشن‌های نصب شده (INSTALLED_APPS) ---

INSTALLED_APPS = [
    # اپ‌های داخلی جنگو
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # مورد نیاز برای SiteSettings

    # اپ‌های پروژه (My Apps)
    'users.apps.UsersConfig',
    'clinic.apps.ClinicConfig',
    'booking.apps.BookingConfig',
    'payment.apps.PaymentConfig',
    'beautyshop_blog.apps.BeautyshopBlogConfig',
    'consultation.apps.ConsultationConfig',
    'reception_panel.apps.ReceptionPanelConfig',
    'site_settings.apps.SiteSettingsConfig',  # اپ تنظیمات سراسری

    # اپ‌های جانبی (Third-party)
    'crispy_forms',
    'crispy_bootstrap5',
    'jalali_date',  # برای تقویم شمسی در ادمین
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'clinic_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # آدرس پوشه 'templates' در ریشه پروژه
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # افزودن اعلان‌ها به تمام تمپلیت‌ها
                'reception_panel.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'clinic_project.wsgi.application'


# --- دیتابیس (Database) ---

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # تنظیمات دیتابیس از متغیر محیطی (برای Production)
    DATABASES = {'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)}
else:
    # اگر DATABASE_URL تنظیم نشده باشد، local.py آن را
    # با SQLite بازنویسی خواهد کرد.
    DATABASES = {}


# --- اعتبارسنجی رمز عبور ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- بین‌المللی‌سازی (Localization) ---
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True


# --- فایل‌های استاتیک و مدیا ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]  # پوشه استاتیک ریشه
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # پوشه آپلودهای کاربران


# --- تنظیمات متفرقه ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1

# --- تنظیمات احراز هویت ---
AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_REDIRECT_URL = 'users:dashboard'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'

# --- تنظیمات Crispy Forms ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --- تنظیمات درگاه پرداخت (زرین‌پال) ---
ZARINPAL_MERCHANT_ID = os.environ.get("ZARINPAL_MERCHANT_ID", "00000000-0000-0000-0000-000000000000")
ZARINPAL_CALLBACK_URL = "http://127.0.0.1:8000/payment/callback/" # (باید در Production بازنویسی شود)

# --- تنظیمات ایمیل (SMTP) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)


# --- تنظیمات منطق کسب و کار (Business Logic) ---

# نرخ تبدیل امتیاز به تومان (برای محاسبه تخفیف)
POINTS_TO_TOMAN_RATE = 100

# نرخ تبدیل پرداخت به امتیاز (برای اعطای امتیاز)
# (توجه: این تنظیم اکنون "منسوخ" (Legacy) شده و
# نرخ واقعی از SiteSettings.load().price_to_points_rate خوانده می‌شود)
PRICE_TO_POINTS_RATE = 1000 

ADMIN_NOTIFICATION_EMAIL = os.environ.get('ADMIN_NOTIFICATION_EMAIL', 'admin@example.com')


# --- تنظیمات تقویم شمسی (jalali_date) ---
JALALI_DATE_DEFAULTS = {
   'Strftime': {
        'date': '%Y/%m/%d',
        'datetime': '%H:%M:%S %Y/%m/%d',
    },
    'Static': {
        'js': [
            'admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.core.js',
            'admin/jquery.ui.datepicker.jalali/scripts/calendar.js',
            'admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.datepicker-cc.js',
            'admin/jquery.ui.datepicker.jalali/scripts/jquery.ui.datepicker-cc-fa.js',
            'admin/js/main.js',
        ],
        'css': {
            'all': [
                'admin/jquery.ui.datepicker.jalali/themes/base/jquery-ui.min.css',
            ]
        }
    },
}