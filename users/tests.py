# users/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser, Profile

class UserTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='password123',
            phone_number='09123456789'
        )
        self.client = Client()

    def test_profile_created_automatically(self):
        """بررسی ایجاد خودکار پروفایل توسط سیگنال"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.points, 0)

    def test_dashboard_context(self):
        """بررسی باگ داشبورد: متغیر appointments باید در کانتکست باشد"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('users:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        # این خط باگ شما را تست می‌کند:
        self.assertIn('appointments', response.context)
        self.assertIn('user_points', response.context)