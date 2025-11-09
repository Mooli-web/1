# booking/urls.py
# فایل اصلاح‌شده: برای وارد کردن ویو از هر دو فایل views.py و api_views.py

from django.urls import path
from . import views
from . import api_views # <-- وارد کردن فایل API

app_name = 'booking'

urlpatterns = [
    path('new/', views.create_booking_view, name='create_booking'),
    
    # --- API URLs ---
    path('api/get-available-slots/', api_views.get_available_slots_api, name='get_available_slots'),
    path('api/get-month-availability/', api_views.get_month_availability_api, name='get_month_availability'),
    path('api/get-services-for-group/', api_views.get_services_for_group_api, name='get_services_for_group'),
    path('api/apply-discount/', api_views.apply_discount_api, name='apply_discount'),
    
    # --- Standard View URL ---
    path('<int:appointment_id>/rate/', views.rate_appointment_view, name='rate_appointment'),
]