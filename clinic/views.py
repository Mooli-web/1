# clinic/views.py
"""
ویوهای صفحات عمومی (استاتیک و داینامیک) سایت.
بهینه‌سازی کوئری‌ها برای افزایش سرعت لود صفحات.
"""

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from .models import Service, PortfolioItem, FAQ, Testimonial, ServiceGroup

def home_view(request: HttpRequest) -> HttpResponse:
    """
    نمایش صفحه اصلی.
    """
    # واکشی گروه‌های خدماتی (معمولا نیازی به جوین سنگین ندارند مگر اینکه عکس یا دستگاه بخواهیم)
    service_groups = ServiceGroup.objects.all()[:6]
    
    # نظرات مشتریان: حتماً به سرویس نیاز داریم، پس select_related می‌زنیم
    testimonials = Testimonial.objects.select_related('service').filter(
        # می‌توان شرط نمایش نظرات با امتیاز بالا را اضافه کرد
        rating__gte=4 
    ).order_by('-created_at')[:3]
    
    context = {
        'service_groups': service_groups, 
        'testimonials': testimonials
    }
    return render(request, 'clinic/home.html', context)

def service_list_view(request: HttpRequest) -> HttpResponse:
    """
    نمایش تمام خدمات.
    چون در تمپلیت احتمالا نام گروه هر خدمت (service.group.name) نمایش داده می‌شود،
    از select_related('group') استفاده می‌کنیم تا از N+1 Query جلوگیری شود.
    """
    services = Service.objects.select_related('group').all()
    return render(request, 'clinic/service_list.html', {'services': services})

def portfolio_gallery_view(request: HttpRequest) -> HttpResponse:
    """
    گالری نمونه کارها.
    مشابه خدمات، برای نمایش نام سرویس مربوطه، بهینه می‌شود.
    """
    portfolio_items = PortfolioItem.objects.select_related('service').order_by('-created_at')
    return render(request, 'clinic/portfolio_gallery.html', {'portfolio_items': portfolio_items})

def faq_view(request: HttpRequest) -> HttpResponse:
    """
    سوالات متداول.
    """
    faqs = FAQ.objects.filter(is_active=True)
    return render(request, 'clinic/faq.html', {'faqs': faqs})