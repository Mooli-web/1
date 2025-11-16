# users/signals.py
"""
سیگنال‌های (Signals) مربوط به اپلیکیشن users.
این سیگنال‌ها اطمینان حاصل می‌کنند که به ازای هر CustomUser
یک آبجکت Profile متناظر وجود داشته باشد.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    سیگنال create_user_profile.
    هنگامی که یک CustomUser "جدید" (created=True) ذخیره می‌شود،
    این تابع اجرا شده و یک آبجکت Profile خالی برای او ایجاد می‌کند.
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    سیگنال save_user_profile.
    هر زمانی که یک CustomUser ذخیره (save) می‌شود،
    این تابع اجرا شده و آبجکت Profile مرتبط با آن را نیز ذخیره می‌کند.
    (این کار برای برخی روابط خاص در جنگو لازم است)
    """
    # اطمینان از اینکه پروفایل وجود دارد (هرچند سیگنال قبلی باید آن را ساخته باشد)
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # اگر به هر دلیلی پروفایل وجود نداشت، آن را ایجاد کن
        Profile.objects.get_or_create(user=instance)