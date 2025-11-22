# users/signals.py
"""
سیگنال‌های ایجاد خودکار پروفایل.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile

@receiver(post_save, sender=CustomUser)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    ایجاد یا به‌روزرسانی پروفایل هنگام ذخیره کاربر.
    استفاده از get_or_create برای جلوگیری از خطای IntegrityError.
    """
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        # اگر کاربر ویرایش شد، مطمئن شو پروفایل دارد
        if not hasattr(instance, 'profile'):
            Profile.objects.create(user=instance)
        else:
            instance.profile.save()