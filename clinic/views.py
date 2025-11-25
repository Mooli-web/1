# clinic/views.py
"""
ویوهای صفحات عمومی (استاتیک و داینامیک) سایت.
بهینه‌سازی کوئری‌ها برای افزایش سرعت لود صفحات و استفاده از کش.
"""

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.views.decorators.cache import cache_page
from .models import Service, PortfolioItem, FAQ, Testimonial, ServiceGroup

def home_view(request: HttpRequest) -> HttpResponse:
    """
    نمایش صفحه اصلی.
    """
    # دریافت گروه‌ها برای نمایش در صفحه اصلی
    service_groups = ServiceGroup.objects.all()[:6]
    
    # دریافت نظرات مثبت برای بخش اعتماد سازی
    testimonials = Testimonial.objects.select_related('service').filter(
        rating__gte=4 
    ).order_by('-created_at')[:3]
    
    context = {
        'service_groups': service_groups, 
        'testimonials': testimonials
    }
    return render(request, 'clinic/home.html', context)

# کش کردن صفحه خدمات برای ۱۵ دقیقه (900 ثانیه)
# تغییرات قیمت در ادمین تا ۱۵ دقیقه بعد اعمال نمی‌شود مگر کش پاک شود
@cache_page(60 * 15)
def service_list_view(request: HttpRequest) -> HttpResponse:
    """
    نمایش تمام خدمات.
    استفاده از prefetch_related برای دریافت خدمات زیرمجموعه هر گروه در یک کوئری بهینه.
    """
    # به جای دریافت سرویس‌ها و گروه بندی در تمپلیت، گروه‌ها را می‌گیریم و سرویس‌ها را به آن‌ها می‌چسبانیم
    # این کار ساختار تمپلیت را منطقی‌تر می‌کند
    groups = ServiceGroup.objects.prefetch_related('services').all()
    
    return render(request, 'clinic/service_list.html', {'groups': groups})

def portfolio_gallery_view(request: HttpRequest) -> HttpResponse:
    """
    گالری نمونه کارها.
    """
    portfolio_items = PortfolioItem.objects.select_related('service').order_by('-created_at')
    return render(request, 'clinic/portfolio_gallery.html', {'portfolio_items': portfolio_items})

def faq_view(request: HttpRequest) -> HttpResponse:
    """
    سوالات متداول.
    """
    faqs = FAQ.objects.filter(is_active=True)
    return render(request, 'clinic/faq.html', {'faqs': faqs})