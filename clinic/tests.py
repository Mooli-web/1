# clinic/tests.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from .models import DiscountCode

class DiscountCodeTest(TestCase):
    
    def test_is_valid_logic(self):
        """تست منطق اعتبار کد تخفیف"""
        now = timezone.now()
        
        # کد معتبر
        valid_code = DiscountCode.objects.create(
            code='VALID',
            discount_type='PERCENTAGE',
            value=10,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            is_active=True
        )
        self.assertTrue(valid_code.is_valid())
        
        # کد منقضی شده
        expired_code = DiscountCode.objects.create(
            code='EXPIRED',
            discount_type='FIXED_AMOUNT',
            value=1000,
            start_date=now - timedelta(days=10),
            end_date=now - timedelta(days=1),
            is_active=True
        )
        self.assertFalse(expired_code.is_valid())
        
        # کد غیرفعال
        inactive_code = DiscountCode.objects.create(
            code='INACTIVE',
            discount_type='PERCENTAGE',
            value=10,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            is_active=False
        )
        self.assertFalse(inactive_code.is_valid())

    def test_date_validation(self):
        """تست جلوگیری از ثبت تاریخ اشتباه"""
        now = timezone.now()
        code = DiscountCode(
            code='BAD_DATE',
            discount_type='PERCENTAGE',
            value=10,
            start_date=now + timedelta(days=5),
            end_date=now # پایان قبل از شروع
        )
        with self.assertRaises(ValidationError):
            code.full_clean()