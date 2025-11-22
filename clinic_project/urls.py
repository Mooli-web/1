# clinic_project/urls.py
"""
مسیرهای اصلی URL پروژه (Root URL Configuration).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Auth (Login, Logout, Reset Password)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Custom Apps
    path('accounts/', include('users.urls')),
    path('booking/', include('booking.urls')),
    path('payment/', include('payment.urls')),
    path('blog/', include('beautyshop_blog.urls')),
    path('consultation/', include('consultation.urls')),
    path('reception/', include('reception_panel.urls')),
    
    # Main Site (Should be last)
    path('', include('clinic.urls')),
]

# سرو کردن فایل‌های مدیا در حالت توسعه
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)