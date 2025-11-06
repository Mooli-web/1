from django.shortcuts import render, get_object_or_404
# --- TASK 4: Import ServiceGroup ---
from .models import Service, PortfolioItem, FAQ, Testimonial, ServiceGroup

def home_view(request):
    # --- TASK 4: Change query to ServiceGroup ---
    service_groups = ServiceGroup.objects.all()[:6]
    
    # --- OPTIMIZED: Added select_related for service name in testimonials ---
    testimonials = Testimonial.objects.select_related('service').all()[:3]
    
    # --- TASK 5: Specialist query removed (already done in provided file) ---
    
    # --- TASK 4: Update context ---
    context = {
        'service_groups': service_groups, 
        'testimonials': testimonials
    }
    return render(request, 'clinic/home.html', context)

def service_list_view(request):
    services = Service.objects.all()
    return render(request, 'clinic/service_list.html', {'services': services})

def portfolio_gallery_view(request):
    portfolio_items = PortfolioItem.objects.all()
    return render(request, 'clinic/portfolio_gallery.html', {'portfolio_items': portfolio_items})

def faq_view(request):
    faqs = FAQ.objects.filter(is_active=True)
    return render(request, 'clinic/faq.html', {'faqs': faqs})

# --- TASK 5: specialist_list_view and specialist_detail_view REMOVED (already done) ---