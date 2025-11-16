# beautyshop_blog/models.py
"""
مدل‌های داده (Data Models) برای اپلیکیشن وبلاگ (beautyshop_blog).
"""

from django.db import models
from django.conf import settings
from django.urls import reverse

class Category(models.Model):
    """
    مدل "دسته‌بندی" مطالب وبلاگ.
    """
    name = models.CharField(max_length=100, verbose_name="نام دسته")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="اسلاگ (نامک)")
    
    class Meta:
        verbose_name = "دسته بندی"
        verbose_name_plural = "دسته بندی‌ها"
        
    def __str__(self): 
        return self.name

class Post(models.Model):
    """
    مدل "پست" (مقاله) وبلاگ.
    """
    title = models.CharField(max_length=200, verbose_name="عنوان")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="اسلاگ (نامک)")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='blog_posts', 
        verbose_name="نویسنده"
    )
    content = models.TextField(verbose_name="محتوا")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    image = models.ImageField(upload_to='blog/', blank=True, null=True, verbose_name="تصویر شاخص")
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='posts', 
        verbose_name="دسته بندی"
    )
    is_published = models.BooleanField(default=True, verbose_name="منتشر شده")
    
    # --- فیلدهای آمار ---
    view_count = models.PositiveIntegerField(
        default=0, 
        verbose_name="تعداد بازدید (واقعی)"
    )
    
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='blog_likes', 
        blank=True, 
        verbose_name="لایک‌ها (واقعی)",
        help_text="کاربرانی که واقعاً این پست را لایک کرده‌اند."
    )
    
    fake_like_count = models.PositiveIntegerField(
        default=0, 
        verbose_name="تعداد لایک دستی (ادمین)",
        help_text="این عدد با لایک‌های واقعی کاربران (در 'total_likes') جمع می‌شود."
    )
    
    class Meta:
        verbose_name = "پست"
        verbose_name_plural = "پست‌ها"
        ordering = ['-created_at']

    def __str__(self): 
        return self.title
        
    def get_absolute_url(self):
        """
        URL منحصر به فرد این پست را برمی‌گرداند.
        (مورد استفاده در تمپلیت‌ها و ادمین)
        """
        return reverse('beautyshop_blog:post_detail', args=[self.slug])
    
    @property
    def total_likes(self):
        """
        محاسبه مجموع لایک‌ها (واقعی + دستی).
        این property در ادمین و تمپلیت‌ها استفاده می‌شود.
        """
        real_likes = self.likes.count()
        return real_likes + self.fake_like_count