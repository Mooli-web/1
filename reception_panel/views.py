# reception_panel/views.py
"""
این فایل شامل ویوهای اصلی و مرکزی پنل پذیرش است:
- لاگین کارمندان
- داشبورد اصلی (مرکز فرماندهی)
- API مربوط به خواندن اعلان‌ها
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, time

from .forms import ReceptionLoginForm
from .decorators import staff_required
from users.models import CustomUser
from booking.models import Appointment
from consultation.models import ConsultationRequest
from .models import Notification


def reception_login_view(request):
    """
    ویو مربوط به لاگین کارمندان (کاربرانی که is_staff=True هستند).
    """
    # اگر کاربر از قبل لاگین کرده و کارمند است، او را به داشبورد هدایت کن
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('reception_panel:dashboard')

    form = ReceptionLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=username, password=password)
        
        # بررسی حیاتی: کاربر باید هم احراز هویت شود و هم 'کارمند' باشد
        if user is not None and user.is_staff:
            login(request, user)
            # ریدایرکت به داشبورد پس از لاگین موفق
            return redirect('reception_panel:dashboard')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است یا شما دسترسی "کارمند" را ندارید.')
    
    return render(request, 'reception_panel/reception_login.html', {'form': form})

# --- داشبورد (بازنویسی شده) ---
@staff_required
def dashboard_view(request):
    """
    داشبورد اصلی پنل پذیرش (مرکز فرماندهی).
    اطلاعات کلیدی و دسترسی‌های سریع را نمایش می‌دهد.
    """
    today = timezone.now().date()
    # تعریف ابتدا و انتهای امروز برای فیلتر زمانی دقیق
    start_of_day = timezone.make_aware(datetime.combine(today, time.min))
    end_of_day = timezone.make_aware(datetime.combine(today, time.max))

    # --- کوئری‌های داشبورد ---

    # ۱. نوبت‌های تایید شده امروز (برای نمایش در لیست "امروز")
    appointments_today = Appointment.objects.filter(
        start_time__range=(start_of_day, end_of_day),
        status='CONFIRMED'
    ).select_related('patient').prefetch_related('services').order_by('start_time')

    # ۲. نوبت‌های در انتظار پرداخت (برای اطلاع‌رسانی)
    pending_appointments = Appointment.objects.filter(
        status='PENDING'
    ).select_related('patient').prefetch_related('services').order_by('created_at')

    # ۳. مشاوره‌های در انتظار پاسخ
    pending_consultations = ConsultationRequest.objects.filter(
        status='PENDING'
    ).select_related('patient').order_by('created_at')
    
    # ۴. آمار کلی
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


# --- API (بدون تغییر) ---
@require_POST
@staff_required
def mark_notifications_as_read_api(request):
    """
    API داخلی برای علامت‌گذاری تمام اعلان‌های خوانده نشده
    کاربر فعلی (کارمند) به عنوان "خوانده شده".
    """
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)