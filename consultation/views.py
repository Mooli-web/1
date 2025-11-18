# consultation/views.py
"""
ویوهای اپلیکیشن consultation.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ConsultationRequest
from users.models import CustomUser
from .forms import ConsultationRequestForm, ConsultationMessageForm
from django.core.exceptions import PermissionDenied
from django.conf import settings
from reception_panel.models import Notification
from django.urls import reverse
import jdatetime # برای تولید عنوان شمسی

@login_required
def request_list_view(request):
    """
    ویو "لیست مشاوره‌ها" (سمت بیمار).
    """
    requests = ConsultationRequest.objects.filter(patient=request.user).order_by('-created_at')
    return render(request, 'consultation/request_list.html', {'requests': requests})

@login_required
def create_request_view(request):
    """
    ویو "ایجاد درخواست مشاوره" جدید (سمت بیمار).
    تغییر: ایجاد خودکار Subject.
    """
    if request.method == 'POST':
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            consultation_request = form.save(commit=False)
            consultation_request.patient = request.user
            
            # --- ایجاد عنوان خودکار ---
            # چون کاربر عنوان را وارد نمی‌کند، ما یک عنوان سیستمی می‌سازیم
            current_date = jdatetime.datetime.now().strftime("%Y/%m/%d")
            consultation_request.subject = f"مشاوره {current_date}"
            
            consultation_request.save()
            
            # --- اطلاع‌رسانی به کارمندان ---
            staff_users = CustomUser.objects.filter(is_staff=True)
            notification_link = request.build_absolute_uri(
                reverse('reception_panel:consultation_detail', args=[consultation_request.pk])
            )
            for staff in staff_users:
                Notification.objects.create(
                    user=staff,
                    message=f"پیام جدید از {consultation_request.patient.username}",
                    link=notification_link
                )
            
            return redirect('consultation:request_detail', pk=consultation_request.pk)
    else:
        form = ConsultationRequestForm()
    return render(request, 'consultation/create_request.html', {'form': form})

@login_required
def request_detail_view(request, pk):
    """
    ویو "جزئیات مشاوره" (صفحه چت) - (سمت بیمار).
    """
    consultation_request_obj = get_object_or_404(
        ConsultationRequest.objects.select_related('patient'),
        pk=pk
    )
    
    # --- بررسی دسترسی ---
    is_patient = (consultation_request_obj.patient == request.user)
    if not is_patient:
        raise PermissionDenied

    messages_list = consultation_request_obj.messages.select_related('user').all().order_by('timestamp')
    
    if request.method == 'POST':
        form = ConsultationMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.request = consultation_request_obj
            message.user = request.user
            message.save()

            # --- اطلاع‌رسانی به کارمندان ---
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
        
    base_template = "base.html"
    
    return render(request, 'consultation/request_detail_shared.html', {
        'consultation_request': consultation_request_obj,
        'messages': messages_list,
        'form': form,
        'base_template': base_template,
    })