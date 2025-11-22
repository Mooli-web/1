# beautyshop_blog/models.py
import os
import uuid
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

def get_image_path(instance, filename):
    """
    تولید مسیر ذخیره‌سازی امن برای تصاویر.
    نام فایل اصلی را دور می‌اندازد و از UUID استفاده می‌کند.
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('blog/images/', filename)

class Category(models.Model):
    """
    مدل دسته‌بندی مقالات.
    """
    name = models.CharField(max_length=100, verbose_name=_("نام دسته"))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_("اسلاگ (نامک)"), allow_unicode=True)
    
    class Meta:
        verbose_name = _("دسته بندی")
        verbose_name_plural = _("دسته بندی‌ها")
        
    def __str__(self): 
        return self.name

    def save(self, *args, **kwargs):
        """تولید خودکار اسلاگ در صورت خالی بودن"""
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

class Post(models.Model):
    """
    مدل پست وبلاگ.
    """
    title = models.CharField(max_length=200, verbose_name=_("عنوان"))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_("اسلاگ (نامک)"), allow_unicode=True)
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='blog_posts', 
        verbose_name=_("نویسنده")
    )
    
    content = models.TextField(verbose_name=_("محتوا"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ ایجاد"))
    
    # استفاده از تابع تغییر نام برای امنیت بیشتر
    image = models.ImageField(
        upload_to=get_image_path, 
        blank=True, 
        null=True, 
        verbose_name=_("تصویر شاخص")
    )
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='posts', 
        verbose_name=_("دسته بندی")
    )
    
    is_published = models.BooleanField(default=True, verbose_name=_("منتشر شده"))
    
    # --- آمار و ارقام ---
    view_count = models.PositiveIntegerField(default=0, verbose_name=_("تعداد بازدید"))
    
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='blog_likes', 
        blank=True, 
        verbose_name=_("لایک‌کنندگان")
    )
    
    # فیلد جدید برای ذخیره تعداد لایک‌های واقعی (Denormalization)
    cached_like_count = models.PositiveIntegerField(
        default=0,
        editable=False, # توسط ادمین قابل ویرایش نیست، خودکار آپدیت می‌شود
        verbose_name=_("تعداد لایک واقعی (کش شده)")
    )

    fake_like_count = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("تعداد لایک دستی (فیک)"),
        help_text=_("این عدد به تعداد لایک‌های واقعی اضافه می‌شود.")
    )
    
    class Meta:
        verbose_name = _("پست")
        verbose_name_plural = _("پست‌ها")
        ordering = ['-created_at']

    def __str__(self): 
        return self.title
        
    def save(self, *args, **kwargs):
        """تولید خودکار اسلاگ فارسی"""
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('beautyshop_blog:post_detail', args=[self.slug])
    
    @property
    def total_likes(self):
        """
        مجموع لایک‌های واقعی (از کش) + لایک‌های فیک.
        این روش بسیار سریع است و نیازی به کوئری ندارد.
        """
        return self.cached_like_count + self.fake_like_count

# --- سیگنال‌ها (Signals) ---
# برای به‌روزرسانی خودکار cached_like_count هنگام تغییر در ManyToMany Field

@receiver(m2m_changed, sender=Post.likes.through)
def update_post_likes_count(sender, instance, action, **kwargs):
    """
    هر زمان کاربری لایک یا آنلایک کرد، فیلد cached_like_count آپدیت شود.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.cached_like_count = instance.likes.count()
        instance.save(update_fields=['cached_like_count'])