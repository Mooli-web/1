# reception_panel/views_patient.py
# فایل جدید: شامل تمام ویوهای مربوط به مدیریت بیماران.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

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
def patient_list_view(request):
    """
    List and search patients.
    """
    query = request.GET.get('q', '')
    patients = CustomUser.objects.filter(role=CustomUser.Role.PATIENT).order_by('-date_joined')
    
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
    return render(request, 'reception_panel/patient_list.html', context)

@staff_required
def patient_create_view(request):
    """
    Create a new patient from the reception panel.
    """
    if request.method == 'POST':
        form = ReceptionPatientCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"بیمار '{user.username}' با موفقیت ایجاد شد.")
            return redirect('reception_panel:patient_list')
    else:
        form = ReceptionPatientCreationForm()
        
    context = {
        'form': form,
        'title': 'ایجاد بیمار جدید'
    }
    # Uses patient_form.html for creation
    return render(request, 'reception_panel/patient_form.html', context)


@staff_required
def patient_detail_view(request, pk):
    """
    Display a full patient profile with tabs for info, appointments,
    transactions, and consultations. Also handles profile update POST.
    """
    patient = get_object_or_404(CustomUser, pk=pk, role=CustomUser.Role.PATIENT)
    
    if request.method == 'POST':
        # This is the POST logic from the old patient_update_view
        u_form = ReceptionPatientUpdateForm(request.POST, instance=patient)
        p_form = ReceptionProfileUpdateForm(request.POST, request.FILES, instance=patient.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f"اطلاعات '{patient.username}' با موفقیت به‌روزرسانی شد.")
            return redirect('reception_panel:patient_detail', pk=patient.pk)
    else:
        # GET request: instantiate the forms
        u_form = ReceptionPatientUpdateForm(instance=patient)
        p_form = ReceptionProfileUpdateForm(instance=patient.profile)

    # Get patient history for other tabs
    patient_appointments = Appointment.objects.filter(patient=patient).prefetch_related('services', 'selected_device').order_by('-start_time')
    patient_transactions = Transaction.objects.filter(appointment__patient=patient).order_by('-created_at')
    patient_consultations = ConsultationRequest.objects.filter(patient=patient).order_by('-created_at')

    context = {
        'patient': patient,
        'u_form': u_form,
        'p_form': p_form,
        'appointments': patient_appointments,
        'transactions': patient_transactions,
        'consultations': patient_consultations,
    }
    return render(request, 'reception_panel/patient_detail.html', context)