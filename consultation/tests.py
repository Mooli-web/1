# consultation/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser
from .models import ConsultationRequest, ConsultationMessage

class ConsultationTests(TestCase):
    def setUp(self):
        # ایجاد کاربر بیمار
        self.patient = CustomUser.objects.create_user(
            username='patient', password='password123', first_name='Ali'
        )
        self.client.login(username='patient', password='password123')
        
        # ایجاد کاربر دیگر برای تست عدم دسترسی
        self.other_user = CustomUser.objects.create_user(
            username='other', password='password123'
        )

    def test_create_consultation_request(self):
        """تست ایجاد درخواست مشاوره جدید"""
        url = reverse('consultation:create_request')
        data = {'description': 'مشکل پوستی دارم'}
        
        response = self.client.post(url, data, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ConsultationRequest.objects.count(), 1)
        req = ConsultationRequest.objects.first()
        self.assertEqual(req.patient, self.patient)
        self.assertIn('مشاوره', req.subject) # تست تولید خودکار عنوان

    def test_request_detail_access(self):
        """تست دسترسی به جزئیات مشاوره"""
        req = ConsultationRequest.objects.create(
            patient=self.patient, 
            subject="Test", 
            description="Desc"
        )
        url = reverse('consultation:request_detail', args=[req.pk])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # تست عدم دسترسی کاربر دیگر
        self.client.logout()
        self.client.login(username='other', password='password123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403) # PermissionDenied

    def test_send_message(self):
        """تست ارسال پیام در چت"""
        req = ConsultationRequest.objects.create(
            patient=self.patient, 
            subject="Test", 
            description="Desc"
        )
        url = reverse('consultation:request_detail', args=[req.pk])
        data = {'message': 'پیام جدید'}
        
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ConsultationMessage.objects.count(), 1)
        self.assertEqual(ConsultationMessage.objects.first().message, 'پیام جدید')