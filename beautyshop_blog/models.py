# a_copy/beautyshop_blog/models.py

from django.db import models
from django.conf import settings
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="اسلاگ (نامک)")
    
    class Meta:
        verbose_name = "دسته بندی"
        verbose_name_plural = "دسته بندی‌ها"
        
    def __str__(self): 
        return self.name

class Post(models.Model):
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
    
    # --- TASK 3: Add stats fields ---
    view_count = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")
    
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='blog_likes', 
        blank=True, 
        verbose_name="لایک‌ها (واقعی)"
    )
    
    # --- ADDED: Field for manual admin likes ---
    fake_like_count = models.PositiveIntegerField(
        default=0, 
        verbose_name="تعداد لایک دستی (ادمین)",
        help_text="این عدد با لایک‌های واقعی کاربران جمع می‌شود."
    )
    
    class Meta:
        verbose_name = "پست"
        verbose_name_plural = "پست‌ها"
        ordering = ['-created_at']

    def __str__(self): 
        return self.title
        
    def get_absolute_url(self):
        return reverse('beautyshop_blog:post_detail', args=[self.slug])
    
    @property
    def total_likes(self):
        # --- UPDATED: Combine real and fake likes ---
        real_likes = self.likes.count()
        return real_likes + self.fake_like_count