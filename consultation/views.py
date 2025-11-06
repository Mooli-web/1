# a_copy/consultation/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ConsultationRequest
from users.models import CustomUser
# from clinic.models import Specialist # <-- REMOVED
from .forms import ConsultationRequestForm, ConsultationMessageForm
# --- REMOVED: Celery task import ---
# from .tasks import send_new_message_notification_email
from django.core.exceptions import PermissionDenied # <-- ADDED
from django.conf import settings # <-- TASK 1.3: Import settings
# --- ADDED: Imports for In-App Notifications ---
from reception_panel.models import Notification
from django.urls import reverse

@login_required
def request_list_view(request):
    requests = ConsultationRequest.objects.filter(patient=request.user).order_by('-created_at')
    return render(request, 'consultation/request_list.html', {'requests': requests})

@login_required
def create_request_view(request):
    if request.method == 'POST':
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            consultation_request = form.save(commit=False)
            consultation_request.patient = request.user
            consultation_request.save()
            
            # --- TASK 3: Create In-App Notification for all staff (replaces Celery) ---
            staff_users = CustomUser.objects.filter(is_staff=True)
            notification_link = request.build_absolute_uri(
                reverse('reception_panel:consultation_detail', args=[consultation_request.pk])
            )
            for staff in staff_users:
                Notification.objects.create(
                    user=staff,
                    message=f"درخواست مشاوره جدید از {consultation_request.patient.username}: {consultation_request.subject}",
                    link=notification_link
                )
            
            return redirect('consultation:request_detail', pk=consultation_request.pk)
    else:
        form = ConsultationRequestForm()
    return render(request, 'consultation/create_request.html', {'form': form})

@login_required
def request_detail_view(request, pk):
    # --- MODIFIED: Allow access if user is patient ONLY ---
    consultation_request_obj = get_object_or_404(
        ConsultationRequest.objects.select_related('patient'), # Removed specialist
        pk=pk
    )
    
    # Check permission
    is_patient = (consultation_request_obj.patient == request.user)
    
    # --- REMOVED: Specialist check ---
    # is_specialist = False
    # ...

    if not is_patient: # <-- CHANGED: Simplified permission check
        raise PermissionDenied

    messages_list = consultation_request_obj.messages.select_related('user').all().order_by('timestamp')
    
    if request.method == 'POST':
        form = ConsultationMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.request = consultation_request_obj
            message.user = request.user
            message.save()

            # --- TASK 3: Notify Admin/Staff when patient sends a message (replaces Celery) ---
            if is_patient:
                staff_users = CustomUser.objects.filter(is_staff=True)
                notification_link = request.build_absolute_uri(
                    reverse('reception_panel:consultation_detail', args=[consultation_request_obj.pk])
                )
                for staff in staff_users:
                    Notification.objects.create(
                        user=staff,
                        message=f"پیام جدید از بیمار در مشاوره: {consultation_request_obj.subject}",
                        link=notification_link
                    )

            return redirect('consultation:request_detail', pk=pk)
    else:
        form = ConsultationMessageForm()
        
    # --- MODIFIED: Choose the correct base template ---
    base_template = "base.html" # <-- CHANGED: Unconditional
    
    return render(request, 'consultation/request_detail_shared.html', {
        # --- FIX: Renamed 'request' to 'consultation_request' ---
        'consultation_request': consultation_request_obj,
        'messages': messages_list,
        'form': form,
        'base_template': base_template, # Pass base template name
    })
