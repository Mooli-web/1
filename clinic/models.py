# clinic/models.py
"""
مدل‌های داده (Data Models) اصلی برای اپلیکیشن clinic.
این مدل‌ها ساختار اطلاعاتی کلینیک، خدمات، دستگاه‌ها،
و ساعات کاری را تعریف می‌کنند.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class WorkHours(models.Model):
    """
    مدل "ساعات کاری".
    این مدل به صورت انعطاف‌پذیر، ساعات کاری را هم برای
    "گروه‌های خدماتی" (عمومی) و هم برای "خدمات خاص" (اختصاصی)
    تعریف می‌کند.
    """
    DAY_CHOICES = [
        (0, 'شنبه'),
        (1, 'یکشنبه'),
        (2, 'دوشنبه'),
        (3, 'سه‌شنبه'),
        (4, 'چهارشنبه'),
        (5, 'پنجشنبه'),
        (6, 'جمعه'),
    ]
    
    class GenderSpecific(models.TextChoices):
        """
        تعیین می‌کند که آیا این ساعت کاری مخصوص جنسیت خاصی است یا خیر.
        (برای فیلتر کردن در تقویم رزرو)
        """
        ALL = 'ALL', 'همه'
        MALE = 'MALE', 'فقط آقایان'
        FEMALE = 'FEMALE', 'فقط بانوان'

    day_of_week = models.IntegerField(
        choices=DAY_CHOICES, 
        verbose_name="روز هفته"
    )
    start_time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان")

    # --- اتصال انعطاف‌پذیر ---
    # یک ساعت کاری یا به "گروه" متصل است (عمومی)
    service_group = models.ForeignKey(
        'ServiceGroup', 
        on_delete=models.CASCADE, 
        related_name='work_hours', 
        null=True, blank=True,
        verbose_name="گروه خدماتی (ساعت کاری عمومی)"
    )
    # یا به "خدمت" متصل است (اختصاصی)
    service = models.ForeignKey(
        'Service', 
        on_delete=models.CASCADE, 
        related_name='work_hours', 
        null=True, blank=True,
        verbose_name="خدمت (ساعت کاری اختصاصی)"
    )
    
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


class Device(models.Model):
    """
    مدل "دستگاه".
    (مثلاً: دستگاه لیزر کندلا، دستگاه هایفو)
    """
    name = models.CharField(max_length=200, verbose_name="نام دستگاه")
    description = models.TextField(blank=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "دستگاه"
        verbose_name_plural = "دستگاه‌ها"

    def __str__(self):
        return self.name

class ServiceGroup(models.Model):
    """
    مدل "گروه خدماتی".
    (مثلاً: خدمات لیزر، خدمات جوانسازی پوست)
    این مدل به عنوان والد برای "خدمات" (زیرگروه‌ها) عمل می‌کند.
    """
    name = models.CharField(max_length=200, verbose_name="نام گروه خدمت")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    
    home_page_image = models.ImageField(
        upload_to='service_groups/', 
        blank=True, 
        null=True, 
        verbose_name="تصویر صفحه اصلی",
        help_text="عکسی که در صفحه اصلی برای این گروه نمایش داده می‌شود."
    )

    allow_multiple_selection = models.BooleanField(
        default=False,
        verbose_name="اجازه انتخاب همزمان چند زیرگروه",
        help_text="اگر فعال باشد، کاربر می‌تواند چند خدمت از این گروه را همزمان انتخاب کند (مثلاً لیزر نواحی مختلف)"
    )
    
    has_devices = models.BooleanField(
        default=False, 
        verbose_name="نیاز به انتخاب دستگاه دارد؟",
        help_text="آیا برای رزرو خدمات این گروه، انتخاب دستگاه الزامی است؟"
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
    """
    مدل "خدمت" (زیرگروه).
    (مثلاً: لیزر فول بادی، تزریق بوتاکس پیشانی)
    هر خدمت باید به یک "گروه خدماتی" تعلق داشته باشد.
    """
    group = models.ForeignKey(
        ServiceGroup,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name="گروه خدمت"
    )
    name = models.CharField(max_length=200, verbose_name="نام خدمت (زیرگروه)")
    description = models.TextField(verbose_name="توضیحات")
    duration = models.PositiveIntegerField(
        help_text="مدت زمان خدمت به دقیقه", 
        verbose_name="مدت زمان (دقیقه)"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        verbose_name="قیمت"
    )
    
    class Meta:
        verbose_name = "خدمت (زیرگروه)"
        verbose_name_plural = "خدمات (زیرگروه‌ها)"

    def __str__(self):
        return f"{self.group.name} - {self.name}"

class PortfolioItem(models.Model):
    """
    مدل "نمونه کار" (گالری قبل و بعد).
    """
    service = models.ForeignKey(
        Service, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='portfolio_items', 
        verbose_name="خدمت مرتبط"
    )
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
    """
    مدل "سوالات متداول".
    """
    question = models.CharField(max_length=255, verbose_name="سوال")
    answer = models.TextField(verbose_name="پاسخ")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    
    class Meta:
        verbose_name = "سوال متداول"
        verbose_name_plural = "سوالات متداول"
        
    def __str__(self): 
        return self.question

class Testimonial(models.Model):
    """
    مدل "نظر مشتری".
    این مدل توسط بیمار پس از "انجام شدن" نوبت (از طریق فرم امتیازدهی) پر می‌شود.
    """
    patient_name = models.CharField(max_length=100, verbose_name="نام بیمار")
    service = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE, 
        verbose_name="خدمت دریافت شده"
    )
    comment = models.TextField(verbose_name="نظر")
    rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], 
        verbose_name="امتیاز"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    
    class Meta:
        verbose_name = "نظر مشتری"
        verbose_name_plural = "نظرات مشتریان"
        
    def __str__(self): 
        return f"نظر از {self.patient_name} برای {self.service.name}"


class DiscountCode(models.Model):
    """
    مدل "کد تخفیف".
    """
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', 'درصدی'
        FIXED_AMOUNT = 'FIXED_AMOUNT', 'مبلغ ثابت'

    code = models.CharField(max_length=50, unique=True, verbose_name="کد تخفیف")
    discount_type = models.CharField(
        max_length=20, 
        choices=DiscountType.choices, 
        verbose_name="نوع تخفیف"
    )
    value = models.PositiveIntegerField(
        verbose_name="مقدار",
        help_text="اگر نوع 'درصدی' است عدد درصد (مثلا 20)، اگر 'مبلغ ثابت' است مبلغ به تومان (مثلا 50000)"
    )
    start_date = models.DateTimeField(default=timezone.now, verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(verbose_name="تاریخ انقضا")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    # --- محدودیت‌های استفاده ---
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="کاربر مخصوص (اختیاری)",
        help_text="اگر کاربری انتخاب شود، این کد فقط برای او قابل استفاده است."
    )
    is_one_time = models.BooleanField(
        default=False, 
        verbose_name="یکبار مصرف",
        help_text="آیا این کد فقط یکبار قابل استفاده است؟ (در کل سیستم)"
    )
    is_used = models.BooleanField(
        default=False, 
        verbose_name="استفاده شده",
        help_text="اگر کد یکبار مصرف باشد، آیا قبلا استفاده شده است؟"
    )
    
    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def __str__(self):
        return self.code

    def is_valid(self):
        """
        متد کمکی برای بررسی اعتبار کد تخفیف در "لحظه کنونی".
        (این متد در API اعمال تخفیف استفاده می‌شود)
        """
        now = timezone.now()
        # شرط پایه: فعال باشد و در بازه زمانی معتبر باشد
        basic_valid = self.is_active and self.start_date <= now <= self.end_date
        
        if not basic_valid:
            return False
            
        # شرط ثانویه: اگر یکبار مصرف بود، نباید قبلا استفاده شده باشد
        if self.is_one_time and self.is_used:
            return False
            
        return True