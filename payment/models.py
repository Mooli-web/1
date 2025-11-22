# payment/models.py
"""
مدل‌های داده مربوط به پرداخت.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from booking.models import Appointment

class Transaction(models.Model):
    """
    مدل تراکنش مالی.
    هر تراکنش متناظر با یک نوبت (Appointment) است.
    """
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', _('در انتظار پرداخت')
        SUCCESS = 'SUCCESS', _('موفق')
        FAILED = 'FAILED', _('ناموفق')

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        verbose_name=_("نوبت مرتبط"),
        related_name='transaction'
    )
    
    amount = models.DecimalField(
        max_digits=12, # افزایش طول برای مبالغ بالا
        decimal_places=0,
        verbose_name=_("مبلغ (تومان)"),
        help_text=_("مبلغ نهایی پرداخت شده.")
    )
    
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        verbose_name=_("وضعیت"),
        db_index=True
    )
    
    authority = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("کد رهگیری درگاه (Authority)"),
        db_index=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("زمان ایجاد")
    )

    class Meta:
        verbose_name = _("تراکنش")
        verbose_name_plural = _("تراکنش‌ها")
        ordering = ['-created_at']

    def __str__(self):
        return f"تراکنش {self.id} | {self.status} | {self.amount} تومان"