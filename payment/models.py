# payment/models.py
"""
مدل‌های داده (Data Models) برای اپلیکیشن payment.
"""

from django.db import models
from booking.models import Appointment

class Transaction(models.Model):
    """
    مدل "تراکنش".
    هر تراکنش به یک "نوبت" (Appointment) متصل است و وضعیت
    پرداخت آن نوبت را ردیابی می‌کند.
    """
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار پرداخت'
        SUCCESS = 'SUCCESS', 'موفق'
        FAILED = 'FAILED', 'ناموفق'

    # ارتباط یک-به-یک: هر نوبت فقط یک تراکنش موفق می‌تواند داشته باشد
    # (اگرچه در این مدل، یک نوبت می‌تواند چند تراکنش ناموفق
    # و یک تراکنش موفق داشته باشد، اما update_or_create در ویو
    # از ایجاد چند تراکنش Pending جلوگیری می‌کند)
    # *اصلاح*: این فیلد باید OneToOneField باشد
    # (بر اساس کد موجود شما، OneToOneField است که صحیح است)
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        verbose_name="نوبت مرتبط"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name="مبلغ (تومان)",
        help_text="مبلغ نهایی پرداخت شده پس از کسر تخفیف‌ها"
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
        verbose_name="کد رهگیری درگاه (Authority)",
        db_index=True  # مهم: این فیلد برای جستجو در Callback باید ایندکس داشته باشد
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