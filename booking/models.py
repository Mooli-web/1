# booking/models.py
import secrets
import string
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from clinic.models import DiscountCode, Device

def generate_tracking_code():
    """تولید یک کد رهگیری ۸ رقمی شامل حروف و اعداد"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))

class Appointment(models.Model):
    """
    مدل نوبت (Appointment).
    """
    
    class AppointmentStatus(models.TextChoices):
        PENDING = 'PENDING', _('در انتظار پرداخت')
        CONFIRMED = 'CONFIRMED', _('تایید شده')
        CANCELED = 'CANCELED', _('لغو شده')
        DONE = 'DONE', _('انجام شده')

    # --- ارتباط با کاربر (اختیاری شده) ---
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # اگر کاربر حذف شد، نوبت نپرد
        related_name='appointments', 
        verbose_name=_("بیمار (عضو)"),
        null=True, blank=True # نال‌پذیر برای مهمانان
    )
    
    # --- اطلاعات مهمان (برای کسانی که اکانت ندارند) ---
    guest_first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("نام مهمان"))
    guest_last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("نام خانوادگی مهمان"))
    guest_phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name=_("شماره تماس مهمان"))
    
    tracking_code = models.CharField(
        max_length=10, 
        unique=True, 
        default=generate_tracking_code,
        verbose_name=_("کد رهگیری"),
        help_text=_("کد یکتا برای پیگیری نوبت")
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
        # نمایش هوشمند نام (کاربر یا مهمان)
        if self.patient:
            name = self.patient.get_full_name() or self.patient.username
        elif self.guest_last_name:
            name = f"{self.guest_first_name} {self.guest_last_name} (مهمان)"
        else:
            name = "ناشناस"
            
        time_str = self.start_time.strftime('%Y-%m-%d %H:%M')
        return f"{name} - {time_str}"

    def get_full_name(self):
        """متد کمکی برای دریافت نام کامل بیمار"""
        if self.patient:
            return self.patient.get_full_name() or self.patient.username
        return f"{self.guest_first_name} {self.guest_last_name}"

    def get_phone_number(self):
        """متد کمکی برای دریافت شماره تماس"""
        if self.patient:
            return self.patient.phone_number
        return self.guest_phone_number

    def get_total_price(self):
        return sum(service.price for service in self.services.all())

    def get_services_display(self):
        return ", ".join([s.name for s in self.services.all()])
    get_services_display.short_description = _("خدمات")