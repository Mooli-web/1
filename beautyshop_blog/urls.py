# beautyshop_blog/urls.py
"""
نقشه‌برداری URLها (URLconf) برای اپلیکیشن beautyshop_blog.
"""

from django.urls import path
from . import views

app_name = 'beautyshop_blog'

urlpatterns = [
    # لیست مقالات
    path('', views.post_list_view, name='post_list'),
    
    # جزئیات مقاله (بر اساس اسلاگ)
    path('<slug:slug>/', views.post_detail_view, name='post_detail'),
    
    # API (AJAX) برای لایک/آنلایک کردن
    path('like-toggle/<int:pk>/', views.like_toggle_view, name='like_toggle'),
]