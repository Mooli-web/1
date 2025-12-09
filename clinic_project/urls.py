# clinic_project/urls.py
"""
مسیرهای اصلی URL پروژه (Root URL Configuration).
مسیرهای احراز هویت به django-allauth ارجاع داده شده‌اند.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic.base import TemplateView

# ایمپورت سایت‌مپ‌هایی که ساختیم
from clinic.sitemaps import StaticViewSitemap, BlogSitemap, ServiceSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogSitemap,
    'service': ServiceSitemap,
}

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # اپلیکیشن‌ها
    path('users/', include('users.urls')), 
    path('booking/', include('booking.urls')),
    path('payment/', include('payment.urls')),
    path('blog/', include('beautyshop_blog.urls')),
    path('consultation/', include('consultation.urls')),
    path('reception/', include('reception_panel.urls')),
    # Main Site (صفحه اصلی)
    path('', include('clinic.urls')),
    # 1. فایل sitemap.xml
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    # 2. فایل robots.txt (متن ساده)
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]




# سرو کردن فایل‌های مدیا در محیط توسعه
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)