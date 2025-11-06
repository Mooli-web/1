# a_copy/payment/models.py

from django.db import models
from booking.models import Appointment

class Transaction(models.Model):
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار پرداخت'
        SUCCESS = 'SUCCESS', 'موفق'
        FAILED = 'FAILED', 'ناموفق'

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        verbose_name="نوبت مرتبط"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name="مبلغ (تومان)"
    )
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        verbose_name="وضعیت"
    )
    authority = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="کد رهگیری درگاه"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد تراکنش"
    )

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"

    def __str__(self):
        return f"تراکنش برای نوبت شماره {self.appointment.id} به مبلغ {self.amount}"