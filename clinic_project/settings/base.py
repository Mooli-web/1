# clinic_project/settings/base.py
"""
تنظیمات "پایه" (Base) پروژه جنگو.
این فایل حاوی تنظیمات مشترک بین محیط‌های Local و Production است.
تنظیمات اختصاصی در فایل‌های local.py و production.py بازنویسی می‌شوند.
"""

import os
from pathlib import Path
import dj_database_url
from datetime import timedelta

# --- مسیرهای پایه ---
# (settings -> clinic_project -> mooli-web)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- بارگذاری متغیرهای محیطی (.env) ---
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    pass

# --- تنظیمات امنیتی کلیدی (مقادیر پیش‌فرض برای توسعه) ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-me-in-prod')

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS_STRING = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = ALLOWED_HOSTS_STRING.split(',') if ALLOWED_HOSTS_STRING else []

CSRF_TRUSTED_ORIGINS_STRING = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1')
CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS_STRING.split(',') if CSRF_TRUSTED_ORIGINS_STRING else []


# --- اپلیکیشن‌ها (Apps) ---
INSTALLED_APPS = [
    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
      'django.contrib.humanize',  # Required for SiteSettings

    # Third-party Apps
    'crispy_forms',
    'crispy_bootstrap5',
    'jalali_date',

    # Local Apps (پروژه ما)
    'users.apps.UsersConfig',
    'clinic.apps.ClinicConfig',
    'booking.apps.BookingConfig',
    'payment.apps.PaymentConfig',
    'beautyshop_blog.apps.BeautyshopBlogConfig',
    'consultation.apps.ConsultationConfig',
    'reception_panel.apps.ReceptionPanelConfig',
    'site_settings.apps.SiteSettingsConfig',
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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # کانتکست اختصاصی پنل پذیرش
                'reception_panel.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'clinic_project.wsgi.application'


# --- دیتابیس (Database) ---
# در local.py اگر این تنظیم خالی باشد، SQLite جایگزین می‌شود.
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {}


# --- اعتبارسنجی رمز عبور ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- زبان و زمان ---
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True


# --- فایل‌های استاتیک و مدیا ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --- تنظیمات پروژه ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1

AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_REDIRECT_URL = 'users:dashboard'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = 'login'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ZarinPal
ZARINPAL_MERCHANT_ID = os.environ.get("ZARINPAL_MERCHANT_ID", "sandbox")
ZARINPAL_CALLBACK_URL = os.environ.get("ZARINPAL_CALLBACK_URL", "http://127.0.0.1:8000/payment/callback/")

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')
ADMIN_NOTIFICATION_EMAIL = os.environ.get('ADMIN_NOTIFICATION_EMAIL', 'admin@example.com')


# --- منطق کسب و کار (Business Logic) ---

# نرخ تبدیل امتیاز به تومان (برای محاسبه تخفیف در booking/utils.py)
POINTS_TO_TOMAN_RATE = 100

# نکته: متغیر PRICE_TO_POINTS_RATE حذف شد چون اکنون از مدل SiteSettings خوانده می‌شود.


# --- Jalali Date Settings ---
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
            'all': ['admin/jquery.ui.datepicker.jalali/themes/base/jquery-ui.min.css']
        }
    },
}   