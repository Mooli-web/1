# a_copy/clinic/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone

# --- TASK 1: New model for WorkHours ---
class WorkHours(models.Model):
    DAY_CHOICES = [
        (0, 'شنبه'),
        (1, 'یکشنبه'),
        (2, 'دوشنبه'),
        (3, 'سه‌شنبه'),
        (4, 'چهارشنبه'),
        (5, 'پنجشنبه'),
        (6, 'جمعه'),
    ]
    
    # --- TASK 9: Add GenderSpecific choices ---
    class GenderSpecific(models.TextChoices):
        ALL = 'ALL', 'همه'
        MALE = 'MALE', 'فقط آقایان'
        FEMALE = 'FEMALE', 'فقط بانوان'

    day_of_week = models.IntegerField(
        choices=DAY_CHOICES, 
        verbose_name="روز هفته"
    )
    start_time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان")

    service_group = models.ForeignKey(
        'ServiceGroup', 
        on_delete=models.CASCADE, 
        related_name='work_hours', 
        null=True, blank=True,
        verbose_name="گروه خدماتی (ساعت کاری عمومی)"
    )
    service = models.ForeignKey(
        'Service', 
        on_delete=models.CASCADE, 
        related_name='work_hours', 
        null=True, blank=True,
        verbose_name="خدمت (ساعت کاری اختصاصی)"
    )
    
    # --- TASK 9: Add gender_specific field ---
    gender_specific = models.CharField(
        max_length=10, 
        choices=GenderSpecific.choices, 
        default=GenderSpecific.ALL, 
        verbose_name="مخصوص جنسیت"
    )

    class Meta:
        verbose_name = "ساعت کاری"
        verbose_name_plural = "ساعات کاری"
        ordering = ['day_of_week', 'start_time']
        constraints = [
            # اطمینان از اینکه یک ساعت کاری یا برای گروه است یا برای خدمت، نه هر دو
            models.CheckConstraint(
                check=models.Q(service_group__isnull=False, service__isnull=True) | 
                      models.Q(service_group__isnull=True, service__isnull=False),
                name='either_group_or_service_workhour'
            )
        ]

    def __str__(self):
        if self.service:
            return f"[خدمت: {self.service.name}] {self.get_day_of_week_display()}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
        if self.service_group:
            return f"[گروه: {self.service_group.name}] {self.get_day_of_week_display()}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
        return f"{self.get_day_of_week_display()}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


# --- TASK 1: ClinicWorkHours model REMOVED ---

# --- TASK 4: New model for Device ---
class Device(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام دستگاه")
    description = models.TextField(blank=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "دستگاه"
        verbose_name_plural = "دستگاه‌ها"

    def __str__(self):
        return self.name

class ServiceGroup(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام گروه خدمت")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    
    # --- ADDED: Image field for the home page ---
    home_page_image = models.ImageField(
        upload_to='service_groups/', 
        blank=True, 
        null=True, 
        verbose_name="تصویر صفحه اصلی",
        help_text="عکسی که در صفحه اصلی برای این گروه نمایش داده می‌شود."
    )
    # --- END ADDED ---

    allow_multiple_selection = models.BooleanField(
        default=False,
        verbose_name="اجازه انتخاب همزمان چند زیرگروه",
        help_text="اگر فعaال باشد، کاربر می‌تواند چند خدمت از این گروه را همزمان انتخاب کند (مثلاً لیزر نواحی مختلف)"
    )
    
    # --- TASK 2: Add has_devices and M2M to Device ---
    has_devices = models.BooleanField(
        default=False, 
        verbose_name="نیاز به انتخاب دستگاه دارد؟"
    )
    available_devices = models.ManyToManyField(
        Device,
        blank=True,
        verbose_name="دستگاه‌های موجود برای این گروه"
    )

    class Meta:
        verbose_name = "گروه خدمت"
        verbose_name_plural = "گروه‌های خدمات"

    def __str__(self):
        return self.name

class Service(models.Model):
    group = models.ForeignKey(
        ServiceGroup,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name="گروه خدمت"
    )
    name = models.CharField(max_length=200, verbose_name="نام خدمت (زیرگروه)")
    description = models.TextField(verbose_name="توضیحات")
    duration = models.PositiveIntegerField(help_text="مدت زمان خدمت به دقیقه", verbose_name="مدت زمان (دقیقه)")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="قیمت")
    
    # --- TASK 2: Remove M2M to Device ---
    # available_devices = models.ManyToManyField(...) # <-- REMOVED

    class Meta:
        verbose_name = "خدمت (زیرگروه)"
        verbose_name_plural = "خدمات (زیرگروه‌ها)"

    def __str__(self):
        return f"{self.group.name} - {self.name}"

class PortfolioItem(models.Model):
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='portfolio_items', verbose_name="خدمت مرتبط")
    title = models.CharField(max_length=200, verbose_name="عنوان نمونه کار")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    before_image = models.ImageField(upload_to='portfolio/before/', verbose_name="تصویر قبل")
    after_image = models.ImageField(upload_to='portfolio/after/', verbose_name="تصویر بعد")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    class Meta:
        verbose_name = "نمونه کار"
        verbose_name_plural = "نمونه کارها"
        
    def __str__(self): 
        return self.title

class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="سوال")
    answer = models.TextField(verbose_name="پاسخ")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    
    class Meta:
        verbose_name = "سوال متداول"
        verbose_name_plural = "سوالات متداول"
        
    def __str__(self): 
        return self.question

class Testimonial(models.Model):
    patient_name = models.CharField(max_length=100, verbose_name="نام بیمار")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="خدمت دریافت شده")
    comment = models.TextField(verbose_name="نظر")
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name="امتیاز")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    
    class Meta:
        verbose_name = "نظر مشتری"
        verbose_name_plural = "نظرات مشتریان"
        
    def __str__(self): 
        return f"نظر از {self.patient_name} برای {self.service.name}"


class DiscountCode(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', 'درصدی'
        FIXED_AMOUNT = 'FIXED_AMOUNT', 'مبلغ ثابت'

    code = models.CharField(max_length=50, unique=True, verbose_name="کد تخفیف")
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, verbose_name="نوع تخفیف")
    value = models.PositiveIntegerField(verbose_name="مقدار") # Either percentage or amount
    start_date = models.DateTimeField(default=timezone.now, verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(verbose_name="تاریخ انقضا")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="کاربر مخصوص (اختیاری)",
        help_text="اگر کاربری انتخاب شود، این کد فقط برای او قابل استفاده است."
    )
    is_one_time = models.BooleanField(default=False, verbose_name="یکبار مصرف")
    is_used = models.BooleanField(default=False, verbose_name="استفاده شده")
    
    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def __str__(self):
        return self.code

    def is_valid(self):
        """Checks if the discount code is currently active and valid."""
        now = timezone.now()
        basic_valid = self.is_active and self.start_date <= now <= self.end_date
        
        if not basic_valid:
            return False
            
        if self.is_one_time and self.is_used:
            return False
            
        return True