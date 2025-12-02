# site_settings/models.py
from django.db import models
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)
        self.set_cache()

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        if cache.get(cls.__name__):
            return cache.get(cls.__name__)
        obj, created = cls.objects.get_or_create(pk=1)
        if created:
            obj.set_cache()
        return obj

    def set_cache(self):
        cache.set(self.__class__.__name__, self, 60 * 60 * 24)

class SiteSettings(SingletonModel):
    # --- تنظیمات عمومی ---
    price_to_points_rate = models.PositiveIntegerField(
        default=1000, 
        verbose_name=_("نرخ تبدیل پرداخت به امتیاز"),
        help_text=_("به ازای هر X تومان، 1 امتیاز تعلق می‌گیرد")
    )
    
    # --- تنظیمات صفحه اصلی (Hero Section) ---
    hero_title = models.CharField(
        max_length=200, 
        default="تجربه درخشش و جوانی؛ حرفه‌ای‌تر از همیشه",
        verbose_name=_("عنوان اصلی صفحه خانه")
    )
    hero_subtitle = models.TextField(
        default="ما با ترکیب تکنولوژی روز و تخصص پزشکی، بهترین نسخه از زیبایی طبیعی شما را نمایان می‌کنیم.",
        verbose_name=_("زیرعنوان صفحه خانه")
    )
    hero_image = models.ImageField(
        upload_to='site/hero/',
        null=True, blank=True,
        verbose_name=_("تصویر اصلی (Hero)")
    )
    
    # --- آمارها ---
    happy_clients_count = models.CharField(max_length=50, default="2000+", verbose_name=_("تعداد مشتریان راضی"))
    years_experience = models.CharField(max_length=50, default="10+", verbose_name=_("سال تجربه"))

    class Meta:
        verbose_name = _("تنظیمات سایت")
        verbose_name_plural = _("تنظیمات سایت")

    def __str__(self):
        return str(_("پیکربندی سایت"))