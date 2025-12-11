# users/models.py
"""
مدل‌های داده‌ای کاربران.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    """
    مدل کاربر سفارشی با قابلیت لاگین با شماره تلفن.
    """
    class Role(models.TextChoices):
        ADMIN = "ADMIN", _("ادمین")
        PATIENT = "PATIENT", _("بیمار")
    
    class Gender(models.TextChoices):
        MALE = 'MALE', _('آقا')
        FEMALE = 'FEMALE', _('خانم')

    phone_number = models.CharField(
        max_length=15, 
        unique=True, 
        null=True,     
        blank=True,    
        verbose_name=_("شماره تلفن"),
        error_messages={
            'unique': _("این شماره تلفن قبلاً ثبت شده است.")
        }
    )
    
    role = models.CharField(
        max_length=50, 
        choices=Role.choices, 
        default=Role.PATIENT, 
        verbose_name=_("نقش کاربری")
    )
    
    gender = models.CharField(
        max_length=10, 
        choices=Gender.choices, 
        verbose_name=_("جنسیت"),
        null=True, 
        blank=True
    )

    # فیلدهای الزامی برای دستور createsuperuser
    REQUIRED_FIELDS = ['phone_number', 'email'] 

    class Meta:
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")

    def __str__(self):
        return self.get_full_name() or self.username

class Profile(models.Model):
    """
    پروفایل تکمیلی کاربر (امتیاز، عکس و ...).
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name=_("کاربر")
    )
    
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True, 
        verbose_name=_("تصویر پروفایل")
    )
    
    points = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("امتیاز وفاداری")
    )

    referral_code = models.CharField(max_length=10, unique=True, blank=True,verbose_name="کد معرف اختصاصی")
    referred_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='referrals',
        verbose_name="معرفی شده توسط"
    )

    class Meta:
        verbose_name = _("پروفایل")
        verbose_name_plural = _("پروفایل‌ها")

    def __str__(self):
        return f"پروفایل {self.user.username}"