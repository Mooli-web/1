# reception_panel/views_appointment.py
# فایل جدید: شامل تمام ویوهای مربوط به مدیریت نوبت‌ها و رزرو دستی.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST

from .decorators import staff_required
from users.models import CustomUser
from booking.models import Appointment


# --- Manual Booking Views ---
@staff_required
def booking_select_patient_view(request):
    query = request.GET.get('q', '')
    patients = CustomUser.objects.filter(role=CustomUser.Role.PATIENT).order_by('last_name', 'first_name')
    
    if query:
        patients = patients.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        )
        
    context = {
        'patients': patients,
        'query': query,
    }
    return render(request, 'reception_panel/booking_select_patient.html', context)

@staff_required
def booking_act_as_view(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id, role=CustomUser.Role.PATIENT)
    request.session['reception_acting_as_patient_id'] = patient.id
    return redirect('booking:create_booking')

# --- Appointment List View ---
@staff_required
def appointment_list_view(request):
    appointments = Appointment.objects.prefetch_related(
        'services', 'patient', 'selected_device'
    ).order_by('-start_time')
    
    context = {
        'appointments': appointments
    }
    return render(request, 'reception_panel/appointment_list.html', context)

# --- Appointment Management Views ---
@staff_required
@require_POST # Ensure this can only be called via POST
def cancel_appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    # Only cancel appointments that are not already done or canceled
    if appointment.status in ['PENDING', 'CONFIRMED']:
        appointment.status = 'CANCELED'
        appointment.save()
        messages.success(request, f"نوبت شماره {appointment.pk} با موفقیت لغو شد.")
        # TODO: Add logic here to refund points/money if needed
    else:
        messages.error(request, "این نوبت در وضعیتی نیست که بتوان آن را لغو کرد.")
    
    # Redirect back to the referrer (e.g., appointment list or patient detail)
    return redirect(request.META.get('HTTP_REFERER', 'reception_panel:appointment_list'))

@staff_required
@require_POST
def mark_appointment_done_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.status == 'CONFIRMED':
        appointment.status = 'DONE'
        appointment.save()
        messages.success(request, f"نوبت شماره {appointment.pk} به 'انجام شده' تغییر یافت.")
        # As requested, no points are awarded for manually marked appointments.
    else:
        messages.error(request, "فقط نوبت‌های 'تایید شده' را می‌توان 'انجام شده' علامت زد.")
        
    return redirect(request.META.get('HTTP_REFERER', 'reception_panel:appointment_list'))