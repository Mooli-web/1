# users/signals.py
"""
سیگنال‌های ایجاد خودکار پروفایل.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile
import secrets

@receiver(post_save, sender=CustomUser)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        # ایجاد پروفایل
        profile, _ = Profile.objects.get_or_create(user=instance)
        
        # تولید کد معرف (اگر ندارد)
        if not profile.referral_code:
            # تولید یک کد 6 رقمی تصادفی (مثلا: A3F9X1)
            profile.referral_code = secrets.token_hex(3).upper()
            profile.save()
    else:
        # اگر کاربر ویرایش شد، مطمئن شو پروفایل دارد
        if not hasattr(instance, 'profile'):
            Profile.objects.create(user=instance)
        else:
            instance.profile.save()