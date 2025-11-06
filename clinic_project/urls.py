from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('users.urls')),
    path('booking/', include('booking.urls')),
    path('payment/', include('payment.urls')),
    path('blog/', include('beautyshop_blog.urls')),
    # path('panel/', include('doctor_panel.urls')), # <-- REMOVED
    path('consultation/', include('consultation.urls')),
    
    # --- ADDED: URL for the new reception panel ---
    path('reception/', include('reception_panel.urls')),
    
    path('', include('clinic.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)