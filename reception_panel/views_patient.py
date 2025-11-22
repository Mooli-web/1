# reception_panel/views_patient.py
"""
مدیریت بیماران.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse

from .forms import (
    ReceptionPatientCreationForm, 
    ReceptionPatientUpdateForm, ReceptionProfileUpdateForm
)
from .decorators import staff_required
from users.models import CustomUser
from booking.models import Appointment
from payment.models import Transaction
from consultation.models import ConsultationRequest

@staff_required
def patient_list_view(request: HttpRequest) -> HttpResponse:
    """لیست و جستجوی بیماران."""
    query = request.GET.get('q', '')
    patients = CustomUser.objects.filter(role=CustomUser.Role.PATIENT).order_by('-date_joined')
    
    if query:
        patients = patients.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        )
        
    return render(request, 'reception_panel/patient_list.html', {'patients': patients, 'query': query})

@staff_required
def patient_create_view(request: HttpRequest) -> HttpResponse:
    """ایجاد بیمار جدید."""
    if request.method == 'POST':
        form = ReceptionPatientCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"بیمار {user.username} ایجاد شد.")
            return redirect('reception_panel:patient_list')
    else:
        form = ReceptionPatientCreationForm()
        
    return render(request, 'reception_panel/patient_form.html', {'form': form, 'title': 'ایجاد بیمار جدید'})

@staff_required
def patient_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """پرونده کامل بیمار."""
    patient = get_object_or_404(CustomUser.objects.select_related('profile'), pk=pk, role=CustomUser.Role.PATIENT)
    
    if request.method == 'POST':
        u_form = ReceptionPatientUpdateForm(request.POST, instance=patient)
        p_form = ReceptionProfileUpdateForm(request.POST, request.FILES, instance=patient.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "اطلاعات بیمار به‌روزرسانی شد.")
            return redirect('reception_panel:patient_detail', pk=patient.pk)
    else:
        u_form = ReceptionPatientUpdateForm(instance=patient)
        p_form = ReceptionProfileUpdateForm(instance=patient.profile)

    # بهینه‌سازی کوئری‌های تب‌ها
    appts = Appointment.objects.filter(patient=patient).select_related(
        'selected_device', 'discount_code'
    ).prefetch_related('services').order_by('-start_time')
    
    txns = Transaction.objects.filter(appointment__patient=patient).order_by('-created_at')
    consults = ConsultationRequest.objects.filter(patient=patient).order_by('-created_at')

    context = {
        'patient': patient,
        'u_form': u_form,
        'p_form': p_form,
        'appointments': appts,
        'transactions': txns,
        'consultations': consults,
    }
    return render(request, 'reception_panel/patient_detail.html', context)