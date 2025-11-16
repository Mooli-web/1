# users/urls.py
"""
نقشه‌برداری URLها (URLconf) برای اپلیکیشن users.
این URLها معمولاً با پیشوند /accounts/ فراخوانی می‌شوند (طبق تنظیمات
فایل urls.py اصلی پروژه).
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # صفحه ثبت‌نام
    path('signup/', views.signup_view, name='signup'),
    
    # داشبورد کاربری
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # صفحه ویرایش پروفایل
    path('profile/', views.profile_update_view, name='profile_update'),
    
    # API داخلی برای خواندن اعلان‌ها
    path('api/notifications/mark-as-read/', views.mark_notifications_as_read_api, name='mark_notifications_as_read'),
]