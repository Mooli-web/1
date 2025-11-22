# payment/urls.py
from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('start/<int:appointment_id>/', views.start_payment_view, name='start_payment'),
    path('callback/', views.payment_callback_view, name='payment_callback'),
]