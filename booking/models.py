# booking/models.py
"""
مدل‌های داده (Data Models) برای اپلیکیشن booking.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from clinic.models import Service, DiscountCode, Device  # ایمپورت مدل‌های وابسته

class Appointment(models.Model):
    """
    مدل اصلی "نوبت" (Appointment).
    این مدل تمام اطلاعات مربوط به یک رزرو را نگهداری می‌کند،
    از جمله بیمار، خدمات، زمان، وضعیت و تخفیف‌های اعمال شده.
    """
    
    class AppointmentStatus(models.TextChoices):
        """
        وضعیت‌های مختلف یک نوبت در طول چرخه حیات آن.
        """
        PENDING = 'PENDING', 'در انتظار پرداخت'
        CONFIRMED = 'CONFIRMED', 'تایید شده'
        CANCELED = 'CANCELED', 'لغو شده'
        DONE = 'DONE', 'انجام شده'

    # --- فیلدهای اصلی ---
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
    
    selected_device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,  # اگر دستگاه حذف شد، نوبت باقی بماند
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
    
    created_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name="زمان ایجاد نوبت"
    )
    
    # --- فیلدهای تخفیف و امتیاز ---
    # این فیلدها در "زمان ایجاد" نوبت محاسبه و ذخیره می‌شوند
    
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
        on_delete=models.SET_NULL,  # اگر کد حذف شد، نوبت باقی بماند
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
    
    # --- فیلدهای سیستمی و وضعیت ---
    
    is_rated = models.BooleanField(
        default=False, 
        verbose_name="امتیازدهی شده",
        help_text="آیا بیمار برای این نوبت (پس از انجام) نظر ثبت کرده است؟"
    )
    
    points_awarded = models.BooleanField(
        default=False, 
        verbose_name="امتیاز اعطا شده",
        help_text="آیا امتیاز این نوبت (پس از انجام) به بیمار داده شده است؟"
    )

    class Meta:
        verbose_name = "نوبت"
        verbose_name_plural = "نوبت‌ها"
        # می‌توان یک ایندکس (Index) برای start_time و status اضافه کرد
        # ordering = ['-start_time'] (اگر در ویوها زیاد استفاده می‌شود)

    def __str__(self):
        """
        نمایش متنی آبجکت نوبت (مفید در ادمین).
        """
        patient_name = self.patient.username if self.patient else "بیمار حذف شده"
        return f"نوبت برای {patient_name} در {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    # --- متدهای کمکی (Helper Methods) ---

    def get_total_price(self):
        """
        محاسبه قیمت "پایه" نوبت (مجموع قیمت خدمات) قبل از هرگونه تخفیف.
        """
        # (توجه: این متد بهینه‌سازی نشده است. اگر خدمات زیاد باشند
        # و این متد در لیست ادمین استفاده شود، باعث N+1 query می‌شود.
        # در این پروژه، 'services' در ویوها prefetch شده که خوب است.)
        return sum(service.price for service in self.services.all())

    def get_total_duration(self):
        """
        محاسبه مدت زمان "کل" نوبت (مجموع مدت زمان خدمات).
        """
        return sum(service.duration for service in self.services.all())
    
    def get_services_display(self):
        """
        نمایش لیستی خوانا از نام خدمات انتخاب شده.
        (مفید برای ادمین و تمپلیت‌ها)
        """
        return ", ".join([service.name for service in self.services.all()])
    
    get_services_display.short_description = "خدمات"