# a_copy/booking/tests.py

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import CustomUser
# --- TASK 5: Remove Specialist ---
from clinic.models import Service, ServiceGroup
from .models import Appointment

class AppointmentModelTest(TestCase):

    def setUp(self):
        """Set up non-modified objects used by all test methods."""
        # Create a patient
        self.patient = CustomUser.objects.create_user(
            username='testpatient', 
            password='password123',
            phone_number='1234567890',
            first_name='Test',
            last_name='Patient'
        )
        
        # --- TASK 5: Remove doctor_user and specialist ---
        
        # Create a service group
        self.group = ServiceGroup.objects.create(
            name='Test Group'
        )

        # Create a service
        self.service = Service.objects.create(
            group=self.group,
            name='Laser Treatment',
            description='A simple laser treatment.',
            duration=30,
            price=500000
        )

    def test_appointment_creation(self):
        """Test that an appointment can be created with the correct details."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=self.service.duration)
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            # --- TASK 5: Remove specialist ---
            start_time=start_time,
            end_time=end_time,
            status='PENDING',
            code_discount_amount=50000,
            points_used=500
        )
        # Add service *after* creation (for M2M)
        appointment.services.add(self.service)
        
        self.assertEqual(appointment.patient.username, 'testpatient')
        # --- TASK 5: Remove specialist assert ---
        self.assertEqual(appointment.get_services_display(), 'Laser Treatment')
        self.assertEqual(appointment.status, 'PENDING')
        self.assertEqual(appointment.points_used, 500)
        # --- TASK 5: Update str assertion ---
        self.assertEqual(str(appointment), f"نوبت برای {self.patient.username} در {start_time.strftime('%Y-%m-%d %H:%M')}")

    def test_default_appointment_status(self):
        """Test the default status of a newly created appointment."""
        start_time = timezone.now() + timedelta(days=2)
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            # --- TASK 5: Remove specialist ---
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30)
        )
        appointment.services.add(self.service)
        
        self.assertEqual(appointment.status, 'PENDING')
        # --- Updated field names from original file ---
        self.assertEqual(appointment.code_discount_amount, 0)
        self.assertEqual(appointment.points_used, 0)