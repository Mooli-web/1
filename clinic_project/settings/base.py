# clinic_project/settings/base.py
"""
تنظیمات پایه (Base) پروژه جنگو.
"""

import os
from pathlib import Path
import dj_database_url
from datetime import timedelta

# --- مسیرهای پایه ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- بارگذاری متغیرهای محیطی ---
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    pass

# --- تنظیمات امنیتی کلیدی ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-me-in-prod')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1').split(',')

# --- اپلیکیشن‌ها (Apps) ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    'crispy_forms',
    'crispy_bootstrap5',
    'jalali_date',

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
    'allauth.account.middleware.AccountMiddleware',
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
                'reception_panel.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'clinic_project.wsgi.application'

# --- پیکربندی دیتابیس ---
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {}

# --- پیکربندی احراز هویت و Allauth ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# تنظیمات رفتاری Allauth (اصلاح شده)
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
# تغییر مهم: تایید ایمیل به حالت اختیاری (یا none) تغییر کرد تا لاگین گیر نکند
ACCOUNT_EMAIL_VERIFICATION = 'none' 
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_UNIQUE_EMAIL = True
LOGIN_REDIRECT_URL = 'users:dashboard'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

ACCOUNT_SIGNUP_FORM_CLASS = 'users.allauth_forms.AllauthSignupForm'

AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_URL = 'account_login'

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

ZARINPAL_MERCHANT_ID = os.environ.get("ZARINPAL_MERCHANT_ID", "sandbox")
ZARINPAL_CALLBACK_URL = os.environ.get("ZARINPAL_CALLBACK_URL", "http://127.0.0.1:8000/payment/callback/")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.chmail.ir')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 465))
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

POINTS_TO_TOMAN_RATE = 100

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