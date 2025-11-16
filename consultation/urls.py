# consultation/urls.py
"""
نقشه‌برداری URLها (URLconf) برای اپلیکیشن consultation.
این URLها مربوط به بخش "بیمار" هستند.
"""

from django.urls import path
from . import views

app_name = 'consultation'

urlpatterns = [
    # لیست مشاوره‌های بیمار
    path('', views.request_list_view, name='request_list'),
    
    # ایجاد درخواست مشاوره جدید
    path('new/', views.create_request_view, name='create_request'),
    
    # مشاهده جزئیات (چت) یک مشاوره
    path('<int:pk>/', views.request_detail_view, name='request_detail'),
]