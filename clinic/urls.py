# clinic/urls.py
"""
نقشه‌برداری URLها (URLconf) برای اپلیکیشن clinic.
این URLها مربوط به صفحات عمومی سایت هستند.
"""

from django.urls import path
from . import views

app_name = 'clinic'

urlpatterns = [
    # صفحه اصلی
    path('', views.home_view, name='home'),
    
    # لیست خدمات
    path('services/', views.service_list_view, name='service_list'),
    
    # گالری نمونه کار
    path('portfolio/', views.portfolio_gallery_view, name='portfolio_gallery'),
    
    # سوالات متداول
    path('faq/', views.faq_view, name='faq'),
    
    # URLهای مربوط به 'specialist' حذف شدند.
]