# a_copy/reception_panel/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse_lazy, reverse # --- ADDED: reverse ---
from django.conf import settings

# --- UPDATED: Import new forms ---
from .forms import (
    ReceptionLoginForm, ReceptionPatientCreationForm, 
    ReceptionPatientUpdateForm, ReceptionProfileUpdateForm,
    ReceptionServiceUpdateForm, WorkHoursFormSet
)
from .decorators import staff_required
from users.models import CustomUser
from django.db.models import Q # For search
# --- UPDATED: Import more models ---
from booking.models import Appointment
from payment.models import Transaction
from consultation.models import ConsultationRequest
from clinic.models import Service, ServiceGroup, WorkHours
# --- END UPDATES ---
from consultation.forms import ConsultationMessageForm
from .models import Notification
from django.http import JsonResponse
from django.views.decorators.http import require_POST
# --- ADDED: Imports for Dashboard ---
from django.utils import timezone
from datetime import datetime, time

def reception_login_view(request):
    """
    Login view for staff members.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('reception_panel:dashboard')

    form = ReceptionLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=username, password=password)
        
        # Check if user is authenticated AND is a staff member
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('reception_panel:dashboard')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است یا شما دسترسی "کارمند" را ندارید.')
    
    return render(request, 'reception_panel/reception_login.html', {'form': form})

# --- REWRITTEN: Dashboard View ---
@staff_required
def dashboard_view(request):
    """
    Main dashboard for the reception panel (Command Center).
    """
    today = timezone.now().date()
    start_of_day = timezone.make_aware(datetime.combine(today, time.min))
    end_of_day = timezone.make_aware(datetime.combine(today, time.max))

    # Get today's confirmed appointments
    appointments_today = Appointment.objects.filter(
        start_time__range=(start_of_day, end_of_day),
        status='CONFIRMED'
    ).select_related('patient').prefetch_related('services').order_by('start_time')

    # Get pending payments
    pending_appointments = Appointment.objects.filter(
        status='PENDING'
    ).select_related('patient').prefetch_related('services').order_by('created_at')

    # Get pending consultations
    pending_consultations = ConsultationRequest.objects.filter(
        status='PENDING'
    ).select_related('patient').order_by('created_at')

    context = {
        'appointments_today': appointments_today,
        'pending_appointments': pending_appointments,
        'pending_consultations': pending_consultations,
        'patient_count': CustomUser.objects.filter(role=CustomUser.Role.PATIENT).count(),
        'today_appointments_count': appointments_today.count(),
    }
    return render(request, 'reception_panel/reception_dashboard.html', context)

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

# --- REMOVED: patient_update_view (logic merged into patient_detail_view) ---

# --- NEW: Patient Detail View (Profile) ---
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


# --- Consultation Views (Unchanged) ---
@staff_required
def consultation_list_view(request):
    requests = ConsultationRequest.objects.select_related('patient').order_by('-created_at')
    return render(request, 'reception_panel/consultation_list.html', {'requests': requests})

@staff_required
def consultation_detail_view(request, pk):
    consultation_request_obj = get_object_or_404(
        ConsultationRequest.objects.select_related('patient'),
        pk=pk
    )
    
    messages_list = consultation_request_obj.messages.select_related('user').all().order_by('timestamp')
    
    if request.method == 'POST':
        form = ConsultationMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.request = consultation_request_obj
            message.user = request.user # Staff user
            message.save()

            if consultation_request_obj.status == 'PENDING':
                consultation_request_obj.status = 'ANSWERED'
                consultation_request_obj.save()

            notification_link = request.build_absolute_uri(
                reverse('consultation:request_detail', args=[consultation_request_obj.pk])
            )
            Notification.objects.create(
                user=consultation_request_obj.patient,
                message=f"پاسخ جدید از پشتیبانی در مشاوره: {consultation_request_obj.subject}",
                link=notification_link
            )
            
            return redirect('reception_panel:consultation_detail', pk=pk)
    else:
        form = ConsultationMessageForm()
        
    context = {
        'consultation_request': consultation_request_obj,
        'messages': messages_list,
        'form': form,
        'base_template': 'reception_panel/reception_base.html',
    }
    return render(request, 'consultation/request_detail_shared.html', context)

# --- Manual Booking Views (Unchanged) ---
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

# --- Appointment List View (Unchanged logic, template will be modified) ---
@staff_required
def appointment_list_view(request):
    appointments = Appointment.objects.prefetch_related(
        'services', 'patient', 'selected_device'
    ).order_by('-start_time')
    
    context = {
        'appointments': appointments
    }
    return render(request, 'reception_panel/appointment_list.html', context)

# --- NEW: Appointment Management Views ---
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

# --- API View (Unchanged) ---
@require_POST
@staff_required
def mark_notifications_as_read_api(request):
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# --- NEW: Service and WorkHours Management Views ---
@staff_required
def service_list_view(request):
    service_groups = ServiceGroup.objects.prefetch_related('services').all()
    context = {
        'service_groups': service_groups
    }
    return render(request, 'reception_panel/service_list.html', context)

@staff_required
def service_update_view(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ReceptionServiceUpdateForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f"خدمت '{service.name}' با موفقیت به‌روزرسانی شد.")
            return redirect('reception_panel:service_list')
    else:
        form = ReceptionServiceUpdateForm(instance=service)
    
    context = {
        'form': form,
        'service': service
    }
    return render(request, 'reception_panel/service_form.html', context)

@staff_required
def work_hours_update_view(request, group_id=None, service_id=None):
    if group_id:
        parent_obj = get_object_or_404(ServiceGroup, pk=group_id)
        queryset = WorkHours.objects.filter(service_group=parent_obj).order_by('day_of_week', 'start_time')
        form_title = f"ویرایش ساعات کاری گروه: {parent_obj.name}"
    elif service_id:
        parent_obj = get_object_or_404(Service, pk=service_id)
        queryset = WorkHours.objects.filter(service=parent_obj).order_by('day_of_week', 'start_time')
        form_title = f"ویرایش ساعات کاری خدمت: {parent_obj.name}"
    else:
        return redirect('reception_panel:service_list')

    if request.method == 'POST':
        formset = WorkHoursFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            # Get new/changed instances, but don't save to DB yet
            instances = formset.save(commit=False) 
            
            for instance in instances:
                # Set the correct foreign key for new forms
                if group_id:
                    instance.service_group = parent_obj
                    instance.service = None # Ensure constraint is met
                elif service_id:
                    instance.service = parent_obj
                    instance.service_group = None # Ensure constraint is met
                
                instance.save() # Commit this instance
            
            # --- MODIFIED: Correctly handle deletions ---
            # Loop through deleted forms and delete objects
            for obj in formset.deleted_objects:
                obj.delete()
            # --- REPLACED: formset.save_m2m() ---

            messages.success(request, "ساعات کاری با موفقیت به‌روزرسانی شد.")
            return redirect('reception_panel:service_list')
    else:
        formset = WorkHoursFormSet(queryset=queryset)

    context = {
        'formset': formset,
        'title': form_title,
    }
    return render(request, 'reception_panel/work_hours_form.html', context)