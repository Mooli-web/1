# consultation/urls.py
from django.urls import path
from . import views

app_name = 'consultation'

urlpatterns = [
    path('', views.request_list_view, name='request_list'),
    path('new/', views.create_request_view, name='create_request'),
    path('<int:pk>/', views.request_detail_view, name='request_detail'),
]