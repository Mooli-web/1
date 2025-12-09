from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # تغییر: استفاده از tracking_code به جای appointment_id برای جلوگیری از حدس زدن
    path('start/<str:tracking_code>/', views.start_payment_view, name='start_payment'),
    path('callback/', views.payment_callback_view, name='payment_callback'),
]