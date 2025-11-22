# beautyshop_blog/urls.py
from django.urls import path
from . import views

app_name = 'beautyshop_blog'

urlpatterns = [
    path('', views.post_list_view, name='post_list'),
    path('<slug:slug>/', views.post_detail_view, name='post_detail'),
    path('like-toggle/<int:pk>/', views.like_toggle_view, name='like_toggle'),
]