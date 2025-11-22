# reception_panel/views.py
"""
ویوهای اصلی پنل پذیرش (لاگین و داشبورد).
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, time

from .forms import ReceptionLoginForm
from .decorators import staff_required
from users.models import CustomUser
from booking.models import Appointment
from consultation.models import ConsultationRequest
from .models import Notification

def reception_login_view(request: HttpRequest) -> HttpResponse:
    """لاگین اختصاصی کارمندان."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('reception_panel:dashboard')

    form = ReceptionLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('reception_panel:dashboard')
        else:
            messages.error(request, 'اطلاعات نادرست است یا دسترسی ندارید.')
    
    return render(request, 'reception_panel/reception_login.html', {'form': form})

@staff_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """داشبورد مدیریت."""
    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, time.min))
    end_of_day = timezone.make_aware(datetime.combine(today, time.max))

    # 1. نوبت‌های امروز (بهینه‌سازی شده)
    appointments_today = Appointment.objects.filter(
        start_time__range=(start_of_day, end_of_day),
        status='CONFIRMED'
    ).select_related('patient').prefetch_related('services').order_by('start_time')

    # 2. نوبت‌های در انتظار
    pending_appointments = Appointment.objects.filter(
        status='PENDING'
    ).select_related('patient').prefetch_related('services').order_by('created_at')

    # 3. مشاوره‌های جدید
    pending_consultations = ConsultationRequest.objects.filter(
        status='PENDING'
    ).select_related('patient').order_by('created_at')
    
    patient_count = CustomUser.objects.filter(role=CustomUser.Role.PATIENT).count()
    today_appointments_count = appointments_today.count()

    context = {
        'appointments_today': appointments_today,
        'pending_appointments': pending_appointments,
        'pending_consultations': pending_consultations,
        'patient_count': patient_count,
        'today_appointments_count': today_appointments_count,
    }
    return render(request, 'reception_panel/reception_dashboard.html', context)

@require_POST
@staff_required
def mark_notifications_as_read_api(request: HttpRequest) -> JsonResponse:
    """API خواندن اعلان‌ها."""
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)