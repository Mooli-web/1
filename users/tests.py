# a_copy/users/tests.py

from django.test import TestCase
from .models import CustomUser, Profile

class UserModelTest(TestCase):

    def setUp(self):
        """یک کاربر برای همه تست‌های این کلاس ایجاد می‌کند."""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpassword123',
            phone_number='09123456789',
            first_name='Test',
            last_name='User'
        )

    def test_user_creation(self):
        """بررسی می‌کند که فیلدهای کاربر به درستی ذخیره شده‌اند."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_profile_is_created_for_new_user(self):
        """
        بررسی می‌کند که آیا به محض ایجاد کاربر، یک پروفایل برای او
        از طریق سیگنال‌ها ایجاد شده است یا خیر.
        """
        try:
            profile = self.user.profile
            self.assertIsInstance(profile, Profile)
        except Profile.DoesNotExist:
            self.fail("Profile was not created for the user upon creation.")

    def test_profile_default_points(self):
        """بررسی می‌کند که امتیاز پروفایل کاربر جدید به طور پیش‌فرض صفر باشد."""
        self.assertEqual(self.user.profile.points, 0)