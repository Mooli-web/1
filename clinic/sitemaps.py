from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from beautyshop_blog.models import Post
from .models import Service

class StaticViewSitemap(Sitemap):
    """صفحات ثابت سایت"""
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return ['clinic:home', 'clinic:service_list', 'clinic:portfolio_gallery', 'clinic:faq', 'beautyshop_blog:post_list']

    def location(self, item):
        return reverse(item)

class BlogSitemap(Sitemap):
    """مقالات وبلاگ"""
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Post.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

class ServiceSitemap(Sitemap):
    """صفحات تکی خدمات (اگر صفحه جزئیات دارند) - فعلا به لیست لینک می‌شوند"""
    changefreq = 'monthly'
    priority = 0.9
    
    def items(self):
        # چون صفحه اختصاصی برای هر سرویس نداریم (فقط لیست است)، فعلا این بخش را خالی یا محدود می‌کنیم
        # اما اگر در آینده صفحه detail برای سرویس ساختید، اینجا اضافه کنید.
        return []