# clinic_project/settings/base.py
"""
تنظیمات پایه (Base) پروژه جنگو.
این فایل حاوی تنظیمات مشترک بین محیط‌های Local و Production است.
تنظیمات اختصاصی احراز هویت (Allauth) در این بخش اضافه شده است.
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
    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # این ماژول برای عملکرد Allauth ضروری است
    'django.contrib.humanize',

    # Third-party Apps (احراز هویت پیشرفته)
    'allauth',
    'allauth.account',
    'allauth.socialaccount', # جهت پشتیبانی از لاگین با شبکه‌های اجتماعی در آینده
    
    # UI Utilities
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
    
    # میدل‌ور اختصاصی Allauth برای مدیریت حساب کاربری
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
                'django.template.context_processors.request', # این پردازشگر برای Allauth الزامی است
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
    # بک‌اند پیش‌فرض جنگو (برای ورود به پنل ادمین)
    'django.contrib.auth.backends.ModelBackend',
    # بک‌اند اختصاصی Allauth (برای لاگین کاربران عادی)
    'allauth.account.auth_backends.AuthenticationBackend',
]

# شناسه سایت در دیتابیس django_site (معمولاً 1 برای لوکال)
SITE_ID = 1

# تنظیمات رفتاری Allauth
ACCOUNT_AUTHENTICATION_METHOD = 'username_email' # امکان ورود با نام کاربری یا ایمیل
ACCOUNT_EMAIL_REQUIRED = True                # دریافت ایمیل هنگام ثبت‌نام اجباری است
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'     # تایید ایمیل الزامی است (کاربر بدون تایید وارد نمی‌شود)
ACCOUNT_USERNAME_REQUIRED = True             # نام کاربری اجباری است
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True   # دریافت مجدد رمز عبور جهت اطمینان
ACCOUNT_UNIQUE_EMAIL = True                  # جلوگیری از ثبت‌نام تکراری با یک ایمیل
LOGIN_REDIRECT_URL = 'users:dashboard'       # مسیر هدایت پس از ورود موفق
ACCOUNT_LOGOUT_REDIRECT_URL = '/'            # مسیر هدایت پس از خروج

# اتصال فرم شخصی‌سازی شده ثبت‌نام (جهت دریافت موبایل و جنسیت)
ACCOUNT_SIGNUP_FORM_CLASS = 'users.allauth_forms.AllauthSignupForm'

# --- مدل کاربر سفارشی ---
AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_URL = 'account_login' # تغییر به URL استاندارد Allauth

# --- سایر تنظیمات (بدون تغییر) ---
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

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ZarinPal
ZARINPAL_MERCHANT_ID = os.environ.get("ZARINPAL_MERCHANT_ID", "sandbox")
ZARINPAL_CALLBACK_URL = os.environ.get("ZARINPAL_CALLBACK_URL", "http://127.0.0.1:8000/payment/callback/")

# clinic_project/settings/base.py

# تنظیمات ایمیل (Chapar / SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.chmail.ir')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 465))
# اگر از پورت 465 استفاده می‌کنید، SSL باید روشن و TLS خاموش باشد
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False') == 'True'

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Business Logic
POINTS_TO_TOMAN_RATE = 100

# Jalali Date Settings
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