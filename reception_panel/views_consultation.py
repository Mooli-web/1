# reception_panel/views_consultation.py
"""
مدیریت مشاوره‌ها.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.http import HttpRequest, HttpResponse

from .decorators import staff_required
from consultation.models import ConsultationRequest
from consultation.forms import ConsultationMessageForm
from .models import Notification

@staff_required
def consultation_list_view(request: HttpRequest) -> HttpResponse:
    """لیست تمام مشاوره‌ها."""
    requests = ConsultationRequest.objects.select_related('patient').order_by('-created_at')
    return render(request, 'reception_panel/consultation_list.html', {'requests': requests})

@staff_required
def consultation_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """چت مشاوره."""
    req_obj = get_object_or_404(ConsultationRequest.objects.select_related('patient'), pk=pk)
    messages_list = req_obj.messages.select_related('user').all().order_by('timestamp')
    
    if request.method == 'POST':
        form = ConsultationMessageForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                msg = form.save(commit=False)
                msg.request = req_obj
                msg.user = request.user
                msg.save()

                if req_obj.status == 'PENDING':
                    req_obj.status = 'ANSWERED'
                    req_obj.save(update_fields=['status'])

                # ارسال اعلان به بیمار
                link = request.build_absolute_uri(reverse('consultation:request_detail', args=[req_obj.pk]))
                Notification.objects.create(
                    user=req_obj.patient,
                    message=f"پاسخ جدید در مشاوره: {req_obj.subject}",
                    link=link
                )
            
            return redirect('reception_panel:consultation_detail', pk=pk)
    else:
        form = ConsultationMessageForm()
        
    context = {
        'consultation_request': req_obj,
        'messages': messages_list,
        'form': form,
        'base_template': 'reception_panel/reception_base.html',
    }
    return render(request, 'consultation/request_detail_shared.html', context)