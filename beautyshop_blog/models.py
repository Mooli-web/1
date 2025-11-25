# beautyshop_blog/models.py
import os
import uuid
import math
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

# --- ارجاع به مدل سرویس برای بازاریابی ---
from clinic.models import Service

def get_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('blog/images/', filename)

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("نام دسته"))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_("اسلاگ (نامک)"), allow_unicode=True)
    
    class Meta:
        verbose_name = _("دسته بندی")
        verbose_name_plural = _("دسته بندی‌ها")
        
    def __str__(self): 
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name=_("عنوان"))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_("اسلاگ (نامک)"), allow_unicode=True)
    
    # --- فیلدهای سئو و UX ---
    meta_description = models.CharField(
        max_length=160, 
        blank=True, 
        verbose_name=_("توضیحات متا (SEO)"),
        help_text=_("خلاصه‌ای جذاب برای نمایش در گوگل (حداکثر ۱۶۰ کاراکتر)")
    )
    reading_time = models.PositiveIntegerField(
        default=0, 
        editable=False,
        verbose_name=_("زمان مطالعه (دقیقه)")
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='blog_posts', 
        verbose_name=_("نویسنده")
    )
    
    # --- اتصال بازاریابی ---
    related_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("سرویس مرتبط (جهت رزرو)"),
        help_text=_("اگر این مقاله درباره خدمت خاصی است، آن را انتخاب کنید تا دکمه رزرو نمایش داده شود.")
    )
    
    content = models.TextField(verbose_name=_("محتوا"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ ایجاد"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاریخ ویرایش"))
    
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
    view_count = models.PositiveIntegerField(default=0, verbose_name=_("تعداد بازدید"))
    
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='blog_likes', 
        blank=True, 
        verbose_name=_("لایک‌کنندگان")
    )
    
    cached_like_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name=_("تعداد لایک واقعی (کش شده)")
    )

    fake_like_count = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("تعداد لایک دستی (فیک)")
    )
    
    class Meta:
        verbose_name = _("پست")
        verbose_name_plural = _("پست‌ها")
        ordering = ['-created_at']

    def __str__(self): 
        return self.title
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
            
        # محاسبه خودکار زمان مطالعه (میانگین ۲۰۰ کلمه در دقیقه)
        if self.content:
            word_count = len(self.content.split())
            read_time = math.ceil(word_count / 200)
            self.reading_time = read_time if read_time > 0 else 1
            
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('beautyshop_blog:post_detail', args=[self.slug])
    
    @property
    def total_likes(self):
        return self.cached_like_count + self.fake_like_count

@receiver(m2m_changed, sender=Post.likes.through)
def update_post_likes_count(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.cached_like_count = instance.likes.count()
        instance.save(update_fields=['cached_like_count'])