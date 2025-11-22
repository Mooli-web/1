# payment/tests.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import CustomUser
from clinic.models import Service, ServiceGroup
from booking.models import Appointment
from .models import Transaction

class TransactionModelTest(TestCase):

    def setUp(self):
        self.patient = CustomUser.objects.create_user(
            username='patient_payment',
            password='password123'
        )
        self.group = ServiceGroup.objects.create(name="Payment Group")
        self.service = Service.objects.create(
            group=self.group,
            name='Service 1', 
            duration=30, 
            price=100000
        )
        
        start_time = timezone.now() + timedelta(days=1)
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30)
        )
        self.appointment.services.add(self.service)

    def test_transaction_creation(self):
        """تست ایجاد صحیح آبجکت تراکنش"""
        transaction = Transaction.objects.create(
            appointment=self.appointment,
            amount=self.appointment.get_total_price(), 
            authority='test_authority_123'
        )
        
        self.assertEqual(transaction.appointment, self.appointment)
        self.assertEqual(transaction.amount, 100000)
        self.assertEqual(transaction.status, 'PENDING')
        self.assertTrue(Transaction.objects.filter(authority='test_authority_123').exists())