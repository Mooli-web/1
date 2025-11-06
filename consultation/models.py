# a_copy/consultation/models.py

from django.db import models
from django.conf import settings

class ConsultationRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار پاسخ'),
        ('ANSWERED', 'پاسخ داده شده'),
        ('CLOSED', 'بسته شده'),
    ]
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='consultation_requests',
        verbose_name="بیمار"
    )
    
    subject = models.CharField(max_length=200, verbose_name="موضوع مشاوره")
    description = models.TextField(verbose_name="شرح درخواست")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    class Meta:
        verbose_name = "درخواست مشاوره"
        verbose_name_plural = "درخواست‌های مشاوره"

    def __str__(self): 
        return f"درخواست از {self.patient.username} - {self.subject}"

class ConsultationMessage(models.Model):
    request = models.ForeignKey(
        ConsultationRequest, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name="درخواست مرتبط"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="کاربر"
    )
    message = models.TextField(verbose_name="متن پیام")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")
    
    class Meta:
        verbose_name = "پیام مشاوره"
        verbose_name_plural = "پیام‌های مشاوره"

    def __str__(self): 
        return f"پیام از {self.user.username}"