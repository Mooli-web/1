# a_copy/reception_panel/urls.py

from django.urls import path
from . import views

app_name = 'reception_panel'

urlpatterns = [
    path('login/', views.reception_login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Patient Management (REFACTORED)
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/new/', views.patient_create_view, name='patient_create'),
    # --- CHANGED: 'patient_update_view' removed, logic merged into 'patient_detail' ---
    path('patients/<int:pk>/', views.patient_detail_view, name='patient_detail'),
    
    # Consultation URLs
    path('consultations/', views.consultation_list_view, name='consultation_list'),
    path('consultations/<int:pk>/', views.consultation_detail_view, name='consultation_detail'),
    
    # Manual Booking URLs
    path('booking/select-patient/', views.booking_select_patient_view, name='booking_select_patient'),
    path('booking/act-as/<int:patient_id>/', views.booking_act_as_view, name='booking_act_as'),
    
    # Appointment List & Management (EXPANDED)
    path('appointments/', views.appointment_list_view, name='appointment_list'),
    # --- ADDED: Appointment management URLs ---
    path('appointments/<int:pk>/cancel/', views.cancel_appointment_view, name='appointment_cancel'),
    path('appointments/<int:pk>/mark-done/', views.mark_appointment_done_view, name='appointment_mark_done'),
    
    # API URL
    path('api/notifications/mark-as-read/', views.mark_notifications_as_read_api, name='mark_notifications_as_read'),
    
    # --- ADDED: Service & WorkHours Management ---
    path('clinic/services/', views.service_list_view, name='service_list'),
    path('clinic/services/<int:pk>/edit/', views.service_update_view, name='service_update'),
    path('clinic/work-hours/group/<int:group_id>/', views.work_hours_update_view, name='work_hours_group_update'),
    path('clinic/work-hours/service/<int:service_id>/', views.work_hours_update_view, name='work_hours_service_update'),
]