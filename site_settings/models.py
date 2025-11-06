from django.db import models

class SingletonModel(models.Model):
    """
    مدل پایه‌ای که تضمین می‌کند تنها یک نمونه (با pk=1) از آن وجود داشته باشد.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # همیشه با pk=1 ذخیره کن
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # اجازه حذف نده
        pass

    @classmethod
    def load(cls):
        # متد کمکی برای بارگذاری یا ایجاد اولین نمونه
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class SiteSettings(SingletonModel):
    """
    مدل Singleton برای نگهداری تنظیمات کلی سایت.
    """
    price_to_points_rate = models.PositiveIntegerField(
        default=1000, 
        verbose_name="نرخ تبدیل پرداخت به امتیاز", 
        help_text="به ازای هر X تومان، 1 امتیاز تعلق می‌گیرد (مثال: 1000)"
    )

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return "تنظیمات سایت"