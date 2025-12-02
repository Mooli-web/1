# clinic/views.py
"""
ویوهای صفحات عمومی (استاتیک و داینامیک) سایت.
بهینه‌سازی کوئری‌ها برای افزایش سرعت لود صفحات.
"""

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.db.models import Prefetch
from .models import Service, PortfolioItem, FAQ, Testimonial, ServiceGroup
from django.core.paginator import Paginator
from site_settings.models import SiteSettings

def home_view(request: HttpRequest) -> HttpResponse:
    """
    نمایش صفحه اصلی با تمام امکانات جدید.
    """
    # 1. تنظیمات سایت (متن‌های هیرو و...)
    settings = SiteSettings.load()

    # 2. خدمات (برای نمایش تمام عرض)
    service_groups = ServiceGroup.objects.prefetch_related('services').all()
    
    # 3. نظرات مشتریان (برای اسلایدر)
    testimonials = Testimonial.objects.select_related('service').filter(
        rating__gte=4 
    ).order_by('-created_at')[:10] # تعداد بیشتر برای اسلایدر

    # 4. نمونه کارهای منتخب (برای اسلایدر قبل و بعد در صفحه اصلی)
    portfolio_samples = PortfolioItem.objects.select_related('service').order_by('-created_at')[:5]
    
    context = {
        'site_settings': settings,
        'service_groups': service_groups, 
        'testimonials': testimonials,
        'portfolio_samples': portfolio_samples,
    }
    return render(request, 'clinic/home.html', context)

def service_list_view(request: HttpRequest) -> HttpResponse:
    """
    نمایش لیست گروه‌بندی شده خدمات.
    بهینه‌سازی: استفاده از prefetch_related برای جلوگیری از مشکل N+1 Query در تمپلیت.
    """
    # دریافت گروه‌ها و پیش‌بارگذاری سرویس‌های فعال هر گروه
    # این کار باعث می‌شود بجای N کوئری، فقط 2 کوئری به دیتابیس زده شود.
    groups = ServiceGroup.objects.prefetch_related(
        Prefetch('services', queryset=Service.objects.all().order_by('price'))
    ).all()
    
    context = {
        'groups': groups, # نام متغیر با تمپلیت هماهنگ شد
    }
    return render(request, 'clinic/service_list.html', context)

def portfolio_gallery_view(request: HttpRequest) -> HttpResponse:
    """
    گالری نمونه کارها.
    بهبودها:
    1. افزودن فیلتر بر اساس گروه خدمات (group_id).
    2. افزودن صفحه‌بندی (Pagination) برای افزایش سرعت لود.
    3. واکشی گروه‌ها برای نمایش در تب‌های فیلتر.
    """
    # دریافت پارامتر فیلتر
    group_id = request.GET.get('group')
    
    # کوئری پایه
    queryset = PortfolioItem.objects.select_related('service__group').order_by('-created_at')
    
    # اعمال فیلتر اگر انتخاب شده باشد
    if group_id:
        queryset = queryset.filter(service__group_id=group_id)
    
    # صفحه‌بندی (نمایش 9 آیتم در هر صفحه)
    paginator = Paginator(queryset, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # دریافت گروه‌هایی که حداقل یک نمونه‌کار دارند (برای نمایش در لیست فیلتر)
    # از distinct استفاده می‌کنیم تا گروه‌های تکراری نیاید
    groups = ServiceGroup.objects.filter(services__portfolio_items__isnull=False).distinct()
    
    context = {
        'portfolio_items': page_obj, # ارسال آبجکت صفحه بجای کل لیست
        'groups': groups,
        'current_group_id': int(group_id) if group_id and group_id.isdigit() else None
    }
    return render(request, 'clinic/portfolio_gallery.html', context)

def faq_view(request: HttpRequest) -> HttpResponse:
    """
    صفحه سوالات متداول.
    شامل: لیست سوالات، دسته‌بندی‌ها و داده‌های ساختاریافته (SEO).
    """
    # دریافت تمام سوالات فعال، مرتب شده بر اساس اولویت
    # استفاده از select_related برای جلوگیری از N+1 Query هنگام دسترسی به category
    faqs = FAQ.objects.select_related('category').filter(is_active=True).order_by('sort_order')
    
    # استخراج دسته‌بندی‌هایی که حداقل یک سوال فعال دارند (برای ساختن تب‌ها)
    # ما از set comprehension پایتون استفاده می‌کنیم تا دیتابیس را دوباره درگیر نکنیم
    # چون faqs را قبلا واکشی کردیم.
    categories = set(faq.category for faq in faqs if faq.category)
    
    context = {
        'faqs': faqs,
        'categories': sorted(list(categories), key=lambda c: c.id), # مرتب‌سازی دسته‌ها
    }
    return render(request, 'clinic/faq.html', context)