# beautyshop_blog/apps.py
from django.apps import AppConfig

class BeautyshopBlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'beautyshop_blog'
    verbose_name = "وبلاگ"
    
    def ready(self):
        # اگر سیگنال‌ها را در فایل جداگانه (signals.py) می‌گذاشتیم، اینجا باید ایمپورت می‌شدند.
        # اما چون در models.py هستند، به صورت خودکار با لود شدن مدل‌ها رجیستر می‌شوند.
        pass