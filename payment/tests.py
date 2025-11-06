# a_copy/payment/tests.py

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import CustomUser
# --- TASK 5: Remove Specialist ---
from clinic.models import Service, ServiceGroup
from booking.models import Appointment
from .models import Transaction

class TransactionModelTest(TestCase):

    def setUp(self):
        """
        یک کاربر، متخصص، سرویس و نوبت برای ایجاد تراکنش آماده می‌کند.
        """
        patient_user = CustomUser.objects.create_user(
            username='patient1',
            password='password123',
            phone_number='09000000000'
        )
        # --- TASK 5: Remove doctor_user and specialist ---

        service_group = ServiceGroup.objects.create(name="Test Group")
        
        service = Service.objects.create(
            group=service_group,
            name='تزریق ژل', 
            duration=30, 
            price=1500000
        )
        start_time = timezone.now() + timedelta(days=5)

        self.appointment = Appointment.objects.create(
            patient=patient_user,
            # --- TASK 5: Remove specialist ---
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30)
        )
        self.appointment.services.add(service)

    def test_transaction_creation(self):
        """
        بررسی می‌کند که یک تراکنش با مقادیر صحیح ایجاد می‌شود.
        """
        transaction = Transaction.objects.create(
            appointment=self.appointment,
            amount=self.appointment.get_total_price(), # Use get_total_price()
            authority='test_authority_123'
        )
        self.assertEqual(transaction.appointment, self.appointment)
        self.assertEqual(transaction.amount, 1500000)
        self.assertEqual(transaction.status, 'PENDING') # Check default status
        self.assertEqual(str(transaction), f"تراکنش برای نوبت شماره {self.appointment.id} به مبلغ {transaction.amount}")