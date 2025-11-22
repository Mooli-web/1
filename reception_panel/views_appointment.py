# reception_panel/views_appointment.py
"""
مدیریت نوبت‌ها توسط پذیرش.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import HttpRequest, HttpResponse

from .decorators import staff_required
from users.models import CustomUser
from booking.models import Appointment

@staff_required
def booking_select_patient_view(request: HttpRequest) -> HttpResponse:
    """انتخاب بیمار برای رزرو دستی."""
    query = request.GET.get('q', '')
    patients = CustomUser.objects.filter(role=CustomUser.Role.PATIENT).order_by('last_name')
    
    if query:
        patients = patients.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        )
        
    return render(request, 'reception_panel/booking_select_patient.html', {'patients': patients, 'query': query})

@staff_required
def booking_act_as_view(request: HttpRequest, patient_id: int) -> HttpResponse:
    """تنظیم نشست برای رزرو به نام بیمار."""
    patient = get_object_or_404(CustomUser, id=patient_id, role=CustomUser.Role.PATIENT)
    request.session['reception_acting_as_patient_id'] = patient.id
    return redirect('booking:create_booking')

@staff_required
def appointment_list_view(request: HttpRequest) -> HttpResponse:
    """لیست کل نوبت‌ها."""
    appointments = Appointment.objects.select_related(
        'patient', 'selected_device', 'discount_code'
    ).prefetch_related('services').order_by('-start_time')
    
    return render(request, 'reception_panel/appointment_list.html', {'appointments': appointments})

@staff_required
@require_POST
def cancel_appointment_view(request: HttpRequest, pk: int) -> HttpResponse:
    """لغو نوبت."""
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.status in ['PENDING', 'CONFIRMED']:
        appointment.status = 'CANCELED'
        appointment.save(update_fields=['status'])
        messages.success(request, "نوبت لغو شد.")
    else:
        messages.error(request, "نوبت قابل لغو نیست.")
    return redirect(request.META.get('HTTP_REFERER', 'reception_panel:appointment_list'))

@staff_required
@require_POST
def mark_appointment_done_view(request: HttpRequest, pk: int) -> HttpResponse:
    """تکمیل نوبت."""
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.status == 'CONFIRMED':
        appointment.status = 'DONE'
        appointment.save(update_fields=['status'])
        messages.success(request, "نوبت انجام شد.")
    else:
        messages.error(request, "فقط نوبت‌های تایید شده قابل انجام هستند.")
    return redirect(request.META.get('HTTP_REFERER', 'reception_panel:appointment_list'))