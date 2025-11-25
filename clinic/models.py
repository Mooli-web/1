# clinic/models.py
import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class WorkHours(models.Model):
    """
    مدل ساعات کاری (عمومی برای گروه یا اختصاصی برای خدمت).
    """
    DAY_CHOICES = [
        (0, _('شنبه')), (1, _('یکشنبه')), (2, _('دوشنبه')), (3, _('سه‌شنبه')),
        (4, _('چهارشنبه')), (5, _('پنجشنبه')), (6, _('جمعه')),
    ]
    
    class GenderSpecific(models.TextChoices):
        ALL = 'ALL', _('همه')
        MALE = 'MALE', _('فقط آقایان')
        FEMALE = 'FEMALE', _('فقط بانوان')

    day_of_week = models.IntegerField(choices=DAY_CHOICES, verbose_name=_("روز هفته"))
    start_time = models.TimeField(verbose_name=_("ساعت شروع"))
    end_time = models.TimeField(verbose_name=_("ساعت پایان"))

    service_group = models.ForeignKey(
        'ServiceGroup', 
        on_delete=models.CASCADE, 
        related_name='work_hours', 
        null=True, blank=True,
        verbose_name=_("گروه خدماتی (عمومی)")
    )
    service = models.ForeignKey(
        'Service', 
        on_delete=models.CASCADE, 
        related_name='work_hours', 
        null=True, blank=True,
        verbose_name=_("خدمت (اختصاصی)")
    )
    
    gender_specific = models.CharField(
        max_length=10, 
        choices=GenderSpecific.choices, 
        default=GenderSpecific.ALL, 
        verbose_name=_("مخصوص جنسیت")
    )

    class Meta:
        verbose_name = _("ساعت کاری")
        verbose_name_plural = _("ساعات کاری")
        ordering = ['day_of_week', 'start_time']
        constraints = [
            models.CheckConstraint(
                check=models.Q(service_group__isnull=False, service__isnull=True) | 
                      models.Q(service_group__isnull=True, service__isnull=False),
                name='either_group_or_service_workhour'
            )
        ]

    def clean(self):
        """اعتبارسنجی سطح مدل"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_("ساعت پایان باید بعد از ساعت شروع باشد."))
        
        if not self.service_group and not self.service:
            raise ValidationError(_("ساعت کاری باید به یک گروه یا یک خدمت متصل باشد."))
            
        if self.service_group and self.service:
            raise ValidationError(_("نمی‌توان همزمان برای گروه و خدمت ساعت کاری تعیین کرد."))

    def __str__(self):
        target = self.service.name if self.service else (self.service_group.name if self.service_group else "Unknown")
        day = self.get_day_of_week_display()
        return f"{target} | {day}: {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"


class Device(models.Model):
    name = models.CharField(max_length=200, verbose_name=_("نام دستگاه"))
    description = models.TextField(blank=True, verbose_name=_("توضیحات"))

    class Meta:
        verbose_name = _("دستگاه")
        verbose_name_plural = _("دستگاه‌ها")

    def __str__(self):
        return self.name

class ServiceGroup(models.Model):
    name = models.CharField(max_length=200, verbose_name=_("نام گروه خدمت"))
    description = models.TextField(blank=True, verbose_name=_("توضیحات"))
    
    home_page_image = models.ImageField(
        upload_to='service_groups/', 
        blank=True, null=True, 
        verbose_name=_("تصویر صفحه اصلی")
    )

    allow_multiple_selection = models.BooleanField(
        default=False,
        verbose_name=_("انتخاب چندگانه"),
        help_text=_("کاربر می‌تواند چند خدمت از این گروه را همزمان انتخاب کند.")
    )
    
    has_devices = models.BooleanField(
        default=False, 
        verbose_name=_("نیاز به دستگاه"),
    )
    available_devices = models.ManyToManyField(
        Device, blank=True, verbose_name=_("دستگاه‌های موجود")
    )

    class Meta:
        verbose_name = _("گروه خدمت")
        verbose_name_plural = _("گروه‌های خدمات")

    def __str__(self):
        return self.name

class Service(models.Model):
    class ServiceBadge(models.TextChoices):
        NONE = 'NONE', '---'
        BEST_SELLER = 'BEST_SELLER', _('پرفروش‌ترین')
        SPECIAL_OFFER = 'SPECIAL_OFFER', _('پیشنهاد ویژه')
        NEW = 'NEW', _('جدید')
        ECONOMICAL = 'ECONOMICAL', _('به‌صرفه')
        LIMITED = 'LIMITED', _('ظرفیت محدود')

    group = models.ForeignKey(
        ServiceGroup,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name=_("گروه خدمت")
    )
    name = models.CharField(max_length=200, verbose_name=_("نام خدمت"))
    description = models.TextField(verbose_name=_("توضیحات"))
    duration = models.PositiveIntegerField(verbose_name=_("مدت زمان (دقیقه)"))
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name=_("قیمت"))
    
    old_price = models.DecimalField(
        max_digits=10, decimal_places=0, null=True, blank=True, 
        verbose_name=_("قیمت خط‌خورده")
    )

    badge = models.CharField(
        max_length=20,
        choices=ServiceBadge.choices,
        default=ServiceBadge.NONE,
        verbose_name=_("برچسب")
    )
    
    class Meta:
        verbose_name = _("خدمت")
        verbose_name_plural = _("خدمات")

    def __str__(self):
        return f"{self.group.name} - {self.name}"
    
    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0
    
def get_portfolio_image_path(instance, filename):
    """
    تولید مسیر امن برای تصاویر نمونه‌کار با استفاده از UUID.
    جلوگیری از تداخل نام فایل‌ها و افشای نام اصلی فایل.
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('portfolio/images/', filename)

class PortfolioItem(models.Model):
    service = models.ForeignKey(
        'Service', # ارجاع رشته‌ای برای جلوگیری از خطای ایمپورت
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='portfolio_items', 
        verbose_name=_("خدمت مرتبط")
    )
    title = models.CharField(max_length=200, verbose_name=_("عنوان"))
    description = models.TextField(blank=True, verbose_name=_("توضیحات"))
    
    # مسیر آپلود اصلاح شد
    before_image = models.ImageField(upload_to=get_portfolio_image_path, verbose_name=_("تصویر قبل"))
    after_image = models.ImageField(upload_to=get_portfolio_image_path, verbose_name=_("تصویر بعد"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ ایجاد"))
    
    class Meta:
        verbose_name = _("نمونه کار")
        verbose_name_plural = _("نمونه کارها")
        ordering = ['-created_at'] # مرتب‌سازی پیش‌فرض
        
    def __str__(self): 
        return self.title

class FAQ(models.Model):
    """
    مدل سوالات متداول با قابلیت دسته‌بندی و ترتیب‌دهی.
    """
    question = models.CharField(max_length=255, verbose_name=_("سوال"))
    answer = models.TextField(verbose_name=_("پاسخ"))
    
    # فیلد جدید: اتصال به گروه خدماتی برای دسته‌بندی (مثلاً سوالات مربوط به لیزر)
    category = models.ForeignKey(
        ServiceGroup, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='faqs',
        verbose_name=_("دسته‌بندی (گروه خدمت)"),
        help_text=_("اگر خالی باشد، در دسته عمومی نمایش داده می‌شود.")
    )
    
    # فیلد جدید: اولویت نمایش
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("اولویت نمایش"))
    
    is_active = models.BooleanField(default=True, verbose_name=_("فعال"))

class Testimonial(models.Model):
    patient_name = models.CharField(max_length=100, verbose_name=_("نام بیمار"))
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, verbose_name=_("خدمت")
    )
    comment = models.TextField(verbose_name=_("نظر"))
    rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], verbose_name=_("امتیاز")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ ثبت"))
    
    class Meta:
        verbose_name = _("نظر مشتری")
        verbose_name_plural = _("نظرات مشتریان")
        # خط ordering = ['sort_order'] را از اینجا حذف کنید اگر وجود دارد
        
    def __str__(self): 
        return f"{self.patient_name} ({self.service.name})"


class DiscountCode(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', _('درصدی')
        FIXED_AMOUNT = 'FIXED_AMOUNT', _('مبلغ ثابت')

    code = models.CharField(max_length=50, unique=True, verbose_name=_("کد تخفیف"), db_index=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, verbose_name=_("نوع"))
    value = models.PositiveIntegerField(verbose_name=_("مقدار"))
    
    start_date = models.DateTimeField(default=timezone.now, verbose_name=_("تاریخ شروع"))
    end_date = models.DateTimeField(verbose_name=_("تاریخ انقضا"))
    is_active = models.BooleanField(default=True, verbose_name=_("فعال"))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_("کاربر اختصاصی")
    )
    is_one_time = models.BooleanField(default=False, verbose_name=_("یکبار مصرف"))
    is_used = models.BooleanField(default=False, verbose_name=_("استفاده شده"))
    
    class Meta:
        verbose_name = _("کد تخفیف")
        verbose_name_plural = _("کدهای تخفیف")

    def clean(self):
        """اعتبارسنجی تاریخ انقضا"""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(_("تاریخ انقضا نمی‌تواند قبل از تاریخ شروع باشد."))

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.is_active: return False
        if not (self.start_date <= now <= self.end_date): return False
        if self.is_one_time and self.is_used: return False
        return True