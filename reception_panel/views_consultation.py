# reception_panel/views_consultation.py
"""
این فایل شامل تمام ویوهای مربوط به مدیریت مشاوره‌های متنی
(Consultations) توسط پنل پذیرش است.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .decorators import staff_required
from consultation.models import ConsultationRequest
from consultation.forms import ConsultationMessageForm
from .models import Notification  # برای ارسال اعلان به بیمار


@staff_required
def consultation_list_view(request):
    """
    لیست تمام درخواست‌های مشاوره (جدید و قدیمی) را نمایش می‌دهد.
    """
    requests = ConsultationRequest.objects.select_related('patient').order_by('-created_at')
    return render(request, 'reception_panel/consultation_list.html', {'requests': requests})

@staff_required
def consultation_detail_view(request, pk):
    """
    نمایش جزئیات یک درخواست مشاوره (صفحه چت).
    این ویو هم برای نمایش پیام‌ها (GET) و هم برای ارسال پاسخ (POST) استفاده می‌شود.
    
    از تمپلیت اشتراکی 'consultation/request_detail_shared.html' استفاده می‌کند.
    """
    consultation_request_obj = get_object_or_404(
        ConsultationRequest.objects.select_related('patient'),
        pk=pk
    )
    
    # واکشی تمام پیام‌های مرتبط با این درخواست
    messages_list = consultation_request_obj.messages.select_related('user').all().order_by('timestamp')
    
    if request.method == 'POST':
        form = ConsultationMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.request = consultation_request_obj
            message.user = request.user  # کاربر ارسال کننده (کارمند پذیرش)
            message.save()

            # اگر این اولین پاسخ به یک درخواست در انتظار بود، وضعیت را عوض کن
            if consultation_request_obj.status == 'PENDING':
                consultation_request_obj.status = 'ANSWERED'
                consultation_request_obj.save()

            # --- ارسال اعلان درون‌برنامه‌ای به بیمار ---
            # ساخت لینک مطلق به صفحه "مشاهده مشاوره" در پنل بیمار
            notification_link = request.build_absolute_uri(
                reverse('consultation:request_detail', args=[consultation_request_obj.pk])
            )
            Notification.objects.create(
                user=consultation_request_obj.patient,  # گیرنده: بیمار
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
        # این متغیر به تمپلیت اشتراکی می‌گوید که از 'base' پنل پذیرش ارث‌بری کند
        'base_template': 'reception_panel/reception_base.html',
    }
    return render(request, 'consultation/request_detail_shared.html', context)