# a_copy/booking/urls.py

from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('new/', views.create_booking_view, name='create_booking'),
    path('api/get-available-slots/', views.get_available_slots_api, name='get_available_slots'),
    
    # --- URL جدید ما ---
    path('api/get-month-availability/', views.get_month_availability_api, name='get_month_availability'),
    # -------------------

    path('api/get-services-for-group/', views.get_services_for_group_api, name='get_services_for_group'),
    path('api/apply-discount/', views.apply_discount_api, name='apply_discount'),
    path('<int:appointment_id>/rate/', views.rate_appointment_view, name='rate_appointment'),
]