# reception_panel/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser

class ReceptionPanelTests(TestCase):
    def setUp(self):
        # کارمند
        self.staff_user = CustomUser.objects.create_user(
            username='staff', password='password123', is_staff=True
        )
        # بیمار
        self.patient_user = CustomUser.objects.create_user(
            username='patient', password='password123', role=CustomUser.Role.PATIENT
        )
        self.client = Client()

    def test_login_required_dashboard(self):
        """دسترسی به داشبورد بدون لاگین باید ریدایرکت شود"""
        url = reverse('reception_panel:dashboard')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, f"{reverse('reception_panel:login')}?next={url}")

    def test_staff_access_dashboard(self):
        """کارمند باید بتواند داشبورد را ببیند"""
        self.client.login(username='staff', password='password123')
        url = reverse('reception_panel:dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_patient_no_access_dashboard(self):
        """بیمار نباید به داشبورد دسترسی داشته باشد"""
        self.client.login(username='patient', password='password123')
        url = reverse('reception_panel:dashboard')
        response = self.client.get(url)
        # به صفحه لاگین پنل پذیرش هدایت می‌شود
        self.assertRedirects(response, f"{reverse('reception_panel:login')}?next={url}")