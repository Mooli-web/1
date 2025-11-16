# beautyshop_blog/apps.py
"""
تنظیمات اپلیکیشن (AppConfig) برای beautyshop_blog.
"""

from django.apps import AppConfig

class BeautyshopBlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'beautyshop_blog'
    verbose_name = "وبلاگ"  # (توصیه می‌شود) افزودن نام فارسی