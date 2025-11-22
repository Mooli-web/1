# reception_panel/urls.py
from django.urls import path
from . import views, views_patient, views_appointment, views_consultation, views_clinic

app_name = 'reception_panel'

urlpatterns = [
    # Core
    path('login/', views.reception_login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/notifications/mark-as-read/', views.mark_notifications_as_read_api, name='mark_notifications_as_read'),

    # Patients
    path('patients/', views_patient.patient_list_view, name='patient_list'),
    path('patients/new/', views_patient.patient_create_view, name='patient_create'),
    path('patients/<int:pk>/', views_patient.patient_detail_view, name='patient_detail'),
    
    # Consultations
    path('consultations/', views_consultation.consultation_list_view, name='consultation_list'),
    path('consultations/<int:pk>/', views_consultation.consultation_detail_view, name='consultation_detail'),
    
    # Appointments
    path('booking/select-patient/', views_appointment.booking_select_patient_view, name='booking_select_patient'),
    path('booking/act-as/<int:patient_id>/', views_appointment.booking_act_as_view, name='booking_act_as'),
    path('appointments/', views_appointment.appointment_list_view, name='appointment_list'),
    path('appointments/<int:pk>/cancel/', views_appointment.cancel_appointment_view, name='appointment_cancel'),
    path('appointments/<int:pk>/mark-done/', views_appointment.mark_appointment_done_view, name='appointment_mark_done'),
    
    # Clinic
    path('clinic/services/', views_clinic.service_list_view, name='service_list'),
    path('clinic/services/<int:pk>/edit/', views_clinic.service_update_view, name='service_update'),
    path('clinic/work-hours/group/<int:group_id>/', views_clinic.work_hours_update_view, name='work_hours_group_update'),
    path('clinic/work-hours/service/<int:service_id>/', views_clinic.work_hours_update_view, name='work_hours_service_update'),
]