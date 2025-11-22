# booking/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from clinic.models import DiscountCode, Device

class Appointment(models.Model):
    """
    مدل نوبت (Appointment).
    """
    
    class AppointmentStatus(models.TextChoices):
        PENDING = 'PENDING', _('در انتظار پرداخت')
        CONFIRMED = 'CONFIRMED', _('تایید شده')
        CANCELED = 'CANCELED', _('لغو شده')
        DONE = 'DONE', _('انجام شده')

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='appointments', 
        verbose_name=_("بیمار")
    )
    
    services = models.ManyToManyField(
        'clinic.Service',
        related_name='appointments',
        verbose_name=_("خدمات انتخاب شده")
    )
    
    selected_device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("دستگاه انتخابی")
    )

    start_time = models.DateTimeField(verbose_name=_("زمان شروع"), db_index=True)
    end_time = models.DateTimeField(verbose_name=_("زمان پایان"), db_index=True)
    
    status = models.CharField(
        max_length=20, 
        choices=AppointmentStatus.choices, 
        default=AppointmentStatus.PENDING,
        verbose_name=_("وضعیت"),
        db_index=True
    )
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("زمان ایجاد"))
    
    # --- مالی و تخفیف ---
    points_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=0, default=0, verbose_name=_("تخفیف امتیاز")
    )
    points_used = models.PositiveIntegerField(default=0, verbose_name=_("امتیاز مصرف شده"))
    
    discount_code = models.ForeignKey(
        DiscountCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("کد تخفیف")
    )
    code_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=0, default=0, verbose_name=_("تخفیف کد")
    )
    
    # --- وضعیت‌های پس از نوبت ---
    is_rated = models.BooleanField(default=False, verbose_name=_("امتیاز داده شده"))
    points_awarded = models.BooleanField(default=False, verbose_name=_("پاداش اعطا شده"))

    class Meta:
        verbose_name = _("نوبت")
        verbose_name_plural = _("نوبت‌ها")
        ordering = ['-start_time']

    def __str__(self):
        patient_name = self.patient.username if self.patient else "Unknown"
        time_str = self.start_time.strftime('%Y-%m-%d %H:%M')
        return f"{patient_name} - {time_str}"

    def get_total_price(self):
        """
        قیمت پایه کل خدمات.
        هشدار: استفاده در حلقه‌ها بدون prefetch_related باعث N+1 Query می‌شود.
        """
        return sum(service.price for service in self.services.all())

    def get_services_display(self):
        return ", ".join([s.name for s in self.services.all()])
    get_services_display.short_description = _("خدمات")