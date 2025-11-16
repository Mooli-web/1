# reception_panel/urls.py
"""
نقشه‌برداری URLها (URLconf) برای اپلیکیشن reception_panel.
این فایل از ساختار تقسیم‌بندی شده (Split Views) استفاده می‌کند
و ویوها را از فایل‌های مجزا (views_patient, views_appointment, ...)
وارد می‌کند.
"""

from django.urls import path
# --- وارد کردن تمام فایل‌های ویو ---
from . import views  # ویوهای اصلی (لاگین، داشبورد، API اعلان)
from . import views_patient  # ویوهای مدیریت بیمار
from . import views_appointment  # ویوهای مدیریت نوبت
from . import views_consultation  # ویوهای مدیریت مشاوره
from . import views_clinic  # ویوهای مدیریت کلینیک (خدمات، ساعات)

app_name = 'reception_panel'

urlpatterns = [
    # --- views.py ---
    path('login/', views.reception_login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/notifications/mark-as-read/', views.mark_notifications_as_read_api, name='mark_notifications_as_read'),

    # --- views_patient.py ---
    path('patients/', views_patient.patient_list_view, name='patient_list'),
    path('patients/new/', views_patient.patient_create_view, name='patient_create'),
    path('patients/<int:pk>/', views_patient.patient_detail_view, name='patient_detail'),
    
    # --- views_consultation.py ---
    path('consultations/', views_consultation.consultation_list_view, name='consultation_list'),
    path('consultations/<int:pk>/', views_consultation.consultation_detail_view, name='consultation_detail'),
    
    # --- views_appointment.py ---
    path('booking/select-patient/', views_appointment.booking_select_patient_view, name='booking_select_patient'),
    path('booking/act-as/<int:patient_id>/', views_appointment.booking_act_as_view, name='booking_act_as'),
    path('appointments/', views_appointment.appointment_list_view, name='appointment_list'),
    path('appointments/<int:pk>/cancel/', views_appointment.cancel_appointment_view, name='appointment_cancel'),
    path('appointments/<int:pk>/mark-done/', views_appointment.mark_appointment_done_view, name='appointment_mark_done'),
    
    # --- views_clinic.py ---
    path('clinic/services/', views_clinic.service_list_view, name='service_list'),
    path('clinic/services/<int:pk>/edit/', views_clinic.service_update_view, name='service_update'),
    path('clinic/work-hours/group/<int:group_id>/', views_clinic.work_hours_update_view, name='work_hours_group_update'),
    path('clinic/work-hours/service/<int:service_id>/', views_clinic.work_hours_update_view, name='work_hours_service_update'),
]