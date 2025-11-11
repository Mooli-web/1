# booking/urls.py
from django.urls import path
from . import views
from . import api_views # <-- وارد کردن فایل API

app_name = 'booking'

urlpatterns = [
    path('new/', views.create_booking_view, name='create_booking'),
    
    # --- API URLs ---
    path('api/all-available-slots/', api_views.all_available_slots_api, name='all_available_slots'),    
    path('api/get-services-for-group/', api_views.get_services_for_group_api, name='get_services_for_group'),
    path('api/apply-discount/', api_views.apply_discount_api, name='apply_discount'),
    path('<int:appointment_id>/rate/', views.rate_appointment_view, name='rate_appointment'),
]