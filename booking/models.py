# a_copy/booking/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
# --- TASK 4: Import Device ---
from clinic.models import Service, DiscountCode, Device

class Appointment(models.Model):
    class AppointmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار پرداخت'
        CONFIRMED = 'CONFIRMED', 'تایید شده'
        CANCELED = 'CANCELED', 'لغو شده'
        DONE = 'DONE', 'انجام شده'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='appointments', 
        verbose_name="بیمار"
    )
    
    services = models.ManyToManyField(
        'clinic.Service',
        related_name='appointments',
        verbose_name="خدمات انتخاب شده"
    )
    
    # --- TASK 4: Add selected_device field ---
    selected_device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="دستگاه انتخابی"
    )

    start_time = models.DateTimeField(verbose_name="زمان شروع")
    end_time = models.DateTimeField(verbose_name="زمان پایان")
    status = models.CharField(
        max_length=20, 
        choices=AppointmentStatus.choices, 
        default=AppointmentStatus.PENDING,
        verbose_name="وضعیت"
    )
    
    points_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        default=0, 
        verbose_name="تخفیف (امتیاز)"
    )
    points_used = models.PositiveIntegerField(
        default=0, 
        verbose_name="امتیاز استفاده شده"
    )
    
    discount_code = models.ForeignKey(
        DiscountCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="کد تخفیف استفاده شده"
    )
    code_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name="تخفیف (کد)"
    )

    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="زمان ایجاد نوبت"
    )
    
    # --- TASK 5: Add is_rated field ---
    is_rated = models.BooleanField(default=False, verbose_name="امتیازدهی شده")
    
    # --- TASK 2: Add points awarded flag ---
    points_awarded = models.BooleanField(default=False, verbose_name="امتیاز اعطا شده")

    class Meta:
        verbose_name = "نوبت"
        verbose_name_plural = "نوبت‌ها"

    def __str__(self):
        return f"نوبت برای {self.patient.username} در {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def get_total_price(self):
        return sum(service.price for service in self.services.all())

    def get_total_duration(self):
        return sum(service.duration for service in self.services.all())
    
    def get_services_display(self):
        return ", ".join([service.name for service in self.services.all()])
    get_services_display.short_description = "خدمات"