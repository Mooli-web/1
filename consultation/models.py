# consultation/models.py
"""
مدل‌های داده (Data Models) برای اپلیکیشن consultation.
"""

from django.db import models
from django.conf import settings

class ConsultationRequest(models.Model):
    """
    مدل "درخواست مشاوره".
    نقطه شروع یک مکالمه (چت) مشاوره است.
    """
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار پاسخ'),  # تازه ایجاد شده
        ('ANSWERED', 'پاسخ داده شده'), # حداقل یک پاسخ از کارمند دریافت کرده
        ('CLOSED', 'بسته شده'),       # بسته شده توسط کارمند
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='consultation_requests',
        verbose_name="بیمار"
    )
    
    subject = models.CharField(max_length=200, verbose_name="موضوع مشاوره")
    description = models.TextField(verbose_name="شرح درخواست (پیام اول)")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING', 
        verbose_name="وضعیت"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    # فیلد 'specialist' از این مدل حذف شده است.
    
    class Meta:
        verbose_name = "درخواست مشاوره"
        verbose_name_plural = "درخواست‌های مشاوره"
        ordering = ['-created_at']

    def __str__(self): 
        return f"درخواست از {self.patient.username} - {self.subject}"

class ConsultationMessage(models.Model):
    """
    مدل "پیام مشاوره".
    هر پیام در یک چت، یک نمونه از این مدل است.
    """
    request = models.ForeignKey(
        ConsultationRequest, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name="درخواست مرتبط"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="کاربر (ارسال کننده)",
        help_text="کاربری که این پیام را ارسال کرده (می‌تواند بیمار یا کارمند باشد)"
    )
    
    message = models.TextField(verbose_name="متن پیام")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")
    
    class Meta:
        verbose_name = "پیام مشاوره"
        verbose_name_plural = "پیام‌های مشاوره"
        ordering = ['timestamp']  # پیام‌ها به ترتیب زمانی نمایش داده می‌شوند

    def __str__(self): 
        return f"پیام از {self.user.username}"