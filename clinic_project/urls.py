# clinic_project/urls.py
"""
نقشه‌برداری URLهای اصلی (Root URLconf) پروژه.
این فایل، آدرس‌های ریشه را به اپلیکیشن‌های مربوطه
(مانند clinic, users, booking, ...) ارجاع می‌دهد.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # پنل ادمین پیش‌فرض جنگو
    path('admin/', admin.site.urls),
    
    # URLهای پیش‌فرض احراز هویت جنگو (login, logout, password_reset, ...)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # URLهای سفارشی کاربران (signup, dashboard, profile)
    path('accounts/', include('users.urls')),
    
    # URLهای اپلیکیشن رزرو نوبت
    path('booking/', include('booking.urls')),
    
    # URLهای اپلیکیشن پرداخت
    path('payment/', include('payment.urls')),
    
    # URLهای اپلیکیشن وبلاگ
    path('blog/', include('beautyshop_blog.urls')),
    
    # URLهای اپلیکیشن مشاوره
    path('consultation/', include('consultation.urls')),
    
    # URLهای اپلیکیشن پنل پذیرش
    path('reception/', include('reception_panel.urls')),
    
    # URLهای اپلیکیشن کلینیک (صفحات عمومی)
    # (این باید "آخرین" مورد باشد تا آدرس ریشه '/' را مدیریت کند)
    path('', include('clinic.urls')),
]

# تنظیمات مربوط به نمایش فایل‌های مدیا (Media) در حالت DEBUG (توسعه)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)