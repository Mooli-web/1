# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_update_view, name='profile_update'),
    path('api/notifications/mark-as-read/', views.mark_notifications_as_read_api, name='mark_notifications_as_read'),
]