# booking/urls.py
"""
نقشه‌برداری URLها (URLconf) برای اپلیکیشن booking.
"""
from django.urls import path
from . import views      # ویوهای اصلی (سمت کاربر)
from . import api_views  # ویوهای API (برای AJAX)

app_name = 'booking'

urlpatterns = [
    # --- ویوهای اصلی ---
    path('new/', views.create_booking_view, name='create_booking'),
    path('<int:appointment_id>/rate/', views.rate_appointment_view, name='rate_appointment'),
    
    # --- API URLs (فراخوانی توسط booking.js) ---
    path('api/all-available-slots/', api_views.all_available_slots_api, name='all_available_slots'),    
    path('api/get-services-for-group/', api_views.get_services_for_group_api, name='get_services_for_group'),
    path('api/apply-discount/', api_views.apply_discount_api, name='apply_discount'),
]