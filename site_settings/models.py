# site_settings/models.py
"""
مدل‌های داده (Data Models) برای اپلیکیشن site_settings.
"""

from django.db import models

class SingletonModel(models.Model):
    """
    مدل پایه‌ای "تک‌نمونه" (Singleton).
    این مدل انتزاعی (abstract) تضمین می‌کند که هر مدلی که از آن
    ارث‌بری می‌کند، همیشه "فقط یک" ردیف (instance) با pk=1
    در دیتابیس داشته باشد.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        بازنویسی (Override) متد save برای اطمینان از اینکه
        این آبجکت همیشه با پرایمری کی (pk) شماره 1 ذخیره می‌شود.
        """
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        بازنویسی متد delete برای جلوگیری از حذف شدن
        این آبجکت Singleton.
        """
        pass  # عملیات حذف نادیده گرفته می‌شود

    @classmethod
    def load(cls):
        """
        متد کمکی (classmethod) برای بارگذاری یا ایجاد اولین نمونه.
        این متد روش استاندارد برای دسترسی به تنظیمات در
        سایر نقاط پروژه است (مثال: SiteSettings.load().price_to_points_rate).
        """
        # اگر آبجکت با pk=1 وجود نداشت، آن را ایجاد می‌کند.
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class SiteSettings(SingletonModel):
    """
    مدل اصلی "تنظیمات سایت".
    این مدل از SingletonModel ارث‌بری می‌کند تا تضمین شود
    همیشه فقط یک نمونه از آن در دیتابیس وجود دارد (با pk=1).
    """
    price_to_points_rate = models.PositiveIntegerField(
        default=1000, 
        verbose_name="نرخ تبدیل پرداخت به امتیاز", 
        help_text="به ازای هر X تومان، 1 امتیاز تعلق می‌گیرد (مثال: 1000)"
    )
    
    # می‌توان تنظیمات سراسری دیگری را در آینده به اینجا اضافه کرد
    # (مثال: هزینه ارسال، درصد مالیات، و ...)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return "تنظیمات سایت"