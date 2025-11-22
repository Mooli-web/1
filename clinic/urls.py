# clinic/urls.py
"""
URLconf برای صفحات عمومی کلینیک.
"""

from django.urls import path
from . import views

app_name = 'clinic'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('services/', views.service_list_view, name='service_list'),
    path('portfolio/', views.portfolio_gallery_view, name='portfolio_gallery'),
    path('faq/', views.faq_view, name='faq'),
]