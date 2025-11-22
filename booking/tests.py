# booking/tests.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import CustomUser
from clinic.models import Service, ServiceGroup
from .models import Appointment

class AppointmentModelTest(TestCase):
    def setUp(self):
        self.patient = CustomUser.objects.create_user(
            username='testpatient', 
            password='password123'
        )
        self.group = ServiceGroup.objects.create(name='Test Group')
        self.service = Service.objects.create(
            group=self.group,
            name='Laser',
            duration=30,
            price=500000
        )

    def test_appointment_creation(self):
        """بررسی ایجاد صحیح نوبت"""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=self.service.duration)
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            start_time=start_time,
            end_time=end_time,
            status='PENDING',
        )
        appointment.services.add(self.service)
        
        self.assertEqual(appointment.patient.username, 'testpatient')
        self.assertEqual(appointment.status, 'PENDING')
        self.assertIn('Laser', appointment.get_services_display())