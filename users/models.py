# users/models.py
"""
مدل‌های داده (Data Models) برای اپلیکیشن users.
شامل مدل سفارشی کاربر (CustomUser) و پروفایل (Profile).
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    """
    مدل کاربر سفارشی (Custom User Model) که جایگزین مدل User پیش‌فرض جنگو شده است.
    - از AbstractUser ارث‌بری می‌کند.
    - شماره تلفن (phone_number) به عنوان فیلد اصلی احراز هویت (در کنار نام کاربری)
      و ایمیل (email) اختیاری است.
    """
    
    class Role(models.TextChoices):
        """نقش‌های کاربری در سیستم."""
        ADMIN = "ADMIN", "ادمین"
        PATIENT = "PATIENT", "بیمار"
    
    class Gender(models.TextChoices):
        """جنسیت کاربر، برای فیلتر کردن ساعات کاری کلینیک."""
        MALE = 'MALE', 'آقا'
        FEMALE = 'FEMALE', 'خانم'

    # بازنویسی فیلد username (در صورت نیاز به حذف ولیدیتورهای پیش‌فرض)
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "الزامی. ۱۵۰ کاراکتر یا کمتر. حروف، اعداد و @/./+/-/_ مجاز است."
        ),
        error_messages={
            "unique": _("کاربری با این نام کاربری از قبل موجود است."),
        },
    )
    
    phone_number = models.CharField(
        max_length=15, 
        unique=True, 
        verbose_name="شماره تلفن",
        help_text="شماره تلفن منحصر به فرد کاربر (برای لاگین و اطلاع‌رسانی)."
    )
    
    role = models.CharField(
        max_length=50, 
        choices=Role.choices, 
        default=Role.PATIENT, 
        verbose_name="نقش"
    )
    
    gender = models.CharField(
        max_length=10, 
        choices=Gender.choices, 
        verbose_name="جنسیت",
        null=True,  # --- مهم: جنسیت اختیاری است ---
        blank=True, # (کاربر ممکن است در زمان ثبت‌نام جنسیت را وارد نکند)
    )

    # تعریف فیلدهای الزامی هنگام ساخت کاربر (createsuperuser)
    # ایمیل (email) حذف شده و شماره تلفن (phone_number) الزامی است.
    REQUIRED_FIELDS = ['phone_number']

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        """نمایش متنی کاربر (نام کامل یا نام کاربری)."""
        return self.get_full_name() or self.username

class Profile(models.Model):
    """
    مدل پروفایل کاربر.
    - ارتباط One-to-One با CustomUser دارد.
    - اطلاعات اضافی مانند امتیاز (points) و تصویر پروفایل را نگهداری می‌کند.
    - این مدل به صورت خودکار توسط سیگنال (signals.py) ایجاد می‌شود.
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        verbose_name="کاربر"
    )
    
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True, 
        verbose_name="تصویر پروفایل"
    )
    
    points = models.PositiveIntegerField(
        default=0, 
        verbose_name="امتیاز",
        help_text="امتیازات قابل استفاده بیمار برای تخفیف."
    )

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self):
        return f"پروفایل {self.user.username}"