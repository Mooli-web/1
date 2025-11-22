# site_settings/models.py
"""
مدل‌های داده برای تنظیمات سایت با قابلیت کش‌گذاری (Caching).
"""

from django.db import models
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

class SingletonModel(models.Model):
    """
    مدل انتزاعی برای پیاده‌سازی الگوی Singleton در دیتابیس.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        ذخیره با شناسه ثابت 1 و پاک‌سازی کش.
        """
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)
        self.set_cache() # آپدیت کش بعد از ذخیره

    def delete(self, *args, **kwargs):
        """
        جلوگیری از حذف فیزیکی.
        """
        pass

    @classmethod
    def load(cls):
        """
        بارگذاری تنظیمات.
        اولویت: 1. کش -> 2. دیتابیس -> 3. ایجاد پیش‌فرض
        """
        # 1. تلاش برای خواندن از کش
        if cache.get(cls.__name__):
            return cache.get(cls.__name__)
        
        # 2. تلاش برای خواندن از دیتابیس یا ایجاد
        obj, created = cls.objects.get_or_create(pk=1)
        
        # 3. ذخیره در کش
        obj.set_cache()
        return obj

    def set_cache(self):
        """
        ذخیره آبجکت فعلی در کش سیستم.
        """
        # کش را برای مدت طولانی (مثلا 24 ساعت) نگه می‌داریم
        # چون با هر بار save، کش آپدیت می‌شود، نگرانی بابت قدیمی بودن نداریم.
        cache.set(self.__class__.__name__, self, 60 * 60 * 24)

class SiteSettings(SingletonModel):
    """
    تنظیمات عمومی سایت.
    """
    price_to_points_rate = models.PositiveIntegerField(
        default=1000, 
        verbose_name=_("نرخ تبدیل پرداخت به امتیاز"), 
        help_text=_("به ازای هر X تومان، 1 امتیاز تعلق می‌گیرد (مثال: 1000)")
    )
    
    # سایر تنظیمات سراسری...

    class Meta:
        verbose_name = _("تنظیمات سایت")
        verbose_name_plural = _("تنظیمات سایت")

    def __str__(self):
        return str(_("پیکربندی سایت"))