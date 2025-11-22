# consultation/models.py
"""
مدل‌های داده برای اپلیکیشن مشاوره.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class ConsultationRequest(models.Model):
    """
    مدل درخواست مشاوره (شروع چت).
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('در انتظار پاسخ')
        ANSWERED = 'ANSWERED', _('پاسخ داده شده')
        CLOSED = 'CLOSED', _('بسته شده')
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='consultation_requests',
        verbose_name=_("بیمار")
    )
    
    subject = models.CharField(max_length=200, verbose_name=_("موضوع مشاوره"))
    description = models.TextField(verbose_name=_("شرح درخواست (پیام اول)"))
    
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING, 
        verbose_name=_("وضعیت"),
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ ایجاد"), db_index=True)
    
    class Meta:
        verbose_name = _("درخواست مشاوره")
        verbose_name_plural = _("درخواست‌های مشاوره")
        ordering = ['-created_at']

    def __str__(self): 
        return f"{self.subject} ({self.patient.username})"

class ConsultationMessage(models.Model):
    """
    مدل پیام‌های رد و بدل شده در یک مشاوره.
    """
    request = models.ForeignKey(
        ConsultationRequest, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name=_("درخواست مرتبط")
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name=_("کاربر (ارسال کننده)")
    )
    
    message = models.TextField(verbose_name=_("متن پیام"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("زمان ارسال"), db_index=True)
    
    class Meta:
        verbose_name = _("پیام مشاوره")
        verbose_name_plural = _("پیام‌های مشاوره")
        ordering = ['timestamp']

    def __str__(self): 
        return f"{self.user.username}: {self.message[:30]}..."