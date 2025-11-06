# a_copy/users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "ادمین"
        PATIENT = "PATIENT", "بیمار"
    
    # --- TASK 8: Add Gender choices ---
    class Gender(models.TextChoices):
        MALE = 'MALE', 'آقا'
        FEMALE = 'FEMALE', 'خانم'

    # --- TASK 1: Override username to remove default validators ---
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "الزامی. ۱۵۰ کاراکتر یا کمتر. حروف، اعداد و @/./+/-/_ مجاز است."
        ),
        # validators=[] # Removed default UnicodeUsernameValidator
        error_messages={
            "unique": _("کاربری با این نام کاربری از قبل موجود است."),
        },
    )
    
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="شماره تلفن")
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.PATIENT, verbose_name="نقش")
    
    # --- TASK 8 / BUG 3 FIX: Made gender optional ---
    gender = models.CharField(
        max_length=10, 
        choices=Gender.choices, 
        verbose_name="جنسیت",
        null=True,  # <-- BUG 3 FIX
        blank=True  # <-- BUG 3 FIX
    )

    # --- ADDED: Make email optional for createsuperuser ---
    REQUIRED_FIELDS = ['phone_number'] # Phone number is required, email is not

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.get_full_name() or self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, verbose_name="کاربر")
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name="تصویر پروفایل")
    points = models.PositiveIntegerField(default=0, verbose_name="امتیاز")

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self):
        return f"پروفایل {self.user.username}"