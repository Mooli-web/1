# consultation/views.py
"""
ویوهای اپلیکیشن مشاوره (سمت بیمار).
"""

import jdatetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.db import transaction
from django.http import HttpRequest, HttpResponse

from .models import ConsultationRequest
from users.models import CustomUser
from .forms import ConsultationRequestForm, ConsultationMessageForm
from reception_panel.models import Notification

@login_required
def request_list_view(request: HttpRequest) -> HttpResponse:
    """
    نمایش لیست درخواست‌های مشاوره کاربر جاری.
    """
    requests = ConsultationRequest.objects.filter(patient=request.user).order_by('-created_at')
    return render(request, 'consultation/request_list.html', {'requests': requests})

@login_required
def create_request_view(request: HttpRequest) -> HttpResponse:
    """
    ایجاد درخواست مشاوره جدید.
    استفاده از transaction.atomic برای تضمین ارسال نوتیفیکیشن همزمان با ایجاد درخواست.
    """
    if request.method == 'POST':
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                consultation_request = form.save(commit=False)
                consultation_request.patient = request.user
                
                # تولید خودکار عنوان بر اساس تاریخ شمسی
                current_date = jdatetime.datetime.now().strftime("%Y/%m/%d")
                consultation_request.subject = f"مشاوره {current_date}"
                
                consultation_request.save()
                
                # ارسال نوتیفیکیشن به تمامی کارمندان (Bulk Create)
                staff_users = CustomUser.objects.filter(is_staff=True)
                if staff_users.exists():
                    notification_link = request.build_absolute_uri(
                        reverse('reception_panel:consultation_detail', args=[consultation_request.pk])
                    )
                    notifications = [
                        Notification(
                            user=staff,
                            message=f"درخواست مشاوره جدید از {consultation_request.patient.get_full_name() or consultation_request.patient.username}",
                            link=notification_link
                        ) for staff in staff_users
                    ]
                    Notification.objects.bulk_create(notifications)
            
            return redirect('consultation:request_detail', pk=consultation_request.pk)
    else:
        form = ConsultationRequestForm()
    return render(request, 'consultation/create_request.html', {'form': form})

@login_required
def request_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    نمایش صفحه چت مشاوره.
    """
    consultation_request_obj = get_object_or_404(
        ConsultationRequest.objects.select_related('patient'),
        pk=pk
    )
    
    # بررسی امنیتی: فقط بیمار صاحب درخواست می‌تواند آن را ببیند
    if consultation_request_obj.patient != request.user:
        raise PermissionDenied

    # واکشی پیام‌ها (با select_related کاربر برای جلوگیری از N+1)
    messages_list = consultation_request_obj.messages.select_related('user').all().order_by('timestamp')
    
    if request.method == 'POST':
        form = ConsultationMessageForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                message = form.save(commit=False)
                message.request = consultation_request_obj
                message.user = request.user
                message.save()

                # ارسال نوتیفیکیشن به کارمندان (Bulk Create)
                staff_users = CustomUser.objects.filter(is_staff=True)
                if staff_users.exists():
                    notification_link = request.build_absolute_uri(
                        reverse('reception_panel:consultation_detail', args=[consultation_request_obj.pk])
                    )
                    notifications = [
                        Notification(
                            user=staff,
                            message=f"پیام جدید از {request.user.username} در مشاوره #{consultation_request_obj.pk}",
                            link=notification_link
                        ) for staff in staff_users
                    ]
                    Notification.objects.bulk_create(notifications)

            return redirect('consultation:request_detail', pk=pk)
    else:
        form = ConsultationMessageForm()
        
    return render(request, 'consultation/request_detail_shared.html', {
        'consultation_request': consultation_request_obj,
        'messages': messages_list,
        'form': form,
        'base_template': "base.html",
    })