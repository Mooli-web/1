# clinic/views.py
"""
این فایل شامل ویوهای عمومی و صفحات اصلی سایت است که
محتوای "ایستا" (Static Pages) یا نمایش عمومی اطلاعات
کلینیک را بر عهده دارند.
"""

from django.shortcuts import render, get_object_or_404
from .models import Service, PortfolioItem, FAQ, Testimonial, ServiceGroup

def home_view(request):
    """
    ویو صفحه اصلی (Home Page).
    - گروه‌های خدماتی (برای نمایش در صفحه)
    - نظرات مشتریان (Testimonials)
    را واکشی کرده و به تمپلیت ارسال می‌کند.
    """
    # واکشی ۶ گروه خدماتی اول (برای نمایش در بلوک‌های صفحه اصلی)
    service_groups = ServiceGroup.objects.all()[:6]
    
    # واکشی ۳ نظر آخر مشتریان (بهینه‌سازی شده با select_related)
    testimonials = Testimonial.objects.select_related('service').all()[:3]
    
    context = {
        'service_groups': service_groups, 
        'testimonials': testimonials
    }
    return render(request, 'clinic/home.html', context)

def service_list_view(request):
    """
    ویو صفحه "لیست خدمات".
    (توجه: بر اساس تمپلیت clinic/service_list.html، این ویو
    در حال حاضر تمام "خدمات" (Services) را لیست می‌کند، نه "گروه‌های خدماتی")
    """
    services = Service.objects.all()
    return render(request, 'clinic/service_list.html', {'services': services})

def portfolio_gallery_view(request):
    """
    ویو صفحه "گالری نمونه کارها" (Portfolio).
    """
    portfolio_items = PortfolioItem.objects.all()
    return render(request, 'clinic/portfolio_gallery.html', {'portfolio_items': portfolio_items})

def faq_view(request):
    """
    ویو صفحه "سوالات متداول" (FAQ).
    فقط سوالات "فعال" (is_active=True) نمایش داده می‌شوند.
    """
    faqs = FAQ.objects.filter(is_active=True)
    return render(request, 'clinic/faq.html', {'faqs': faqs})

# --- ویوهای مربوط به specialist_list و specialist_detail ---
# --- به دلیل حذف مفهوم "متخصص" (Specialist) از پروژه، ---
# --- این ویوها به طور کامل حذف شدند. ---