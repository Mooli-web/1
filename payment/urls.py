# payment/urls.py
"""
نقشه‌برداری URLها (URLconf) برای اپلیکیشن payment.
"""

from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # URL برای شروع فرآیند پرداخت (هدایت به درگاه)
    path('start/<int:appointment_id>/', views.start_payment_view, name='start_payment'),
    
    # URL بازگشت از درگاه (Callback)
    path('callback/', views.payment_callback_view, name='payment_callback'),
]