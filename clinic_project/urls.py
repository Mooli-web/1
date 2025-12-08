# clinic_project/urls.py
"""
مسیرهای اصلی URL پروژه (Root URL Configuration).
مسیرهای احراز هویت به django-allauth ارجاع داده شده‌اند.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),
    
    # Authentication (مدیریت شده توسط Allauth)
    # شامل: ورود، ثبت‌نام، خروج، تایید ایمیل، تغییر رمز عبور
    path('accounts/', include('allauth.urls')),
    
    # Local Apps
    # توجه: ویوی ثبت‌نام (signup) قدیمی در users.urls دیگر استفاده نمی‌شود
    # زیرا allauth مسیر accounts/signup/ را مدیریت می‌کند.
    path('users/', include('users.urls')), 
    path('booking/', include('booking.urls')),
    path('payment/', include('payment.urls')),
    path('blog/', include('beautyshop_blog.urls')),
    path('consultation/', include('consultation.urls')),
    path('reception/', include('reception_panel.urls')),
    
    # Main Site (صفحه اصلی)
    path('', include('clinic.urls')),
]

# سرو کردن فایل‌های مدیا در محیط توسعه
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)