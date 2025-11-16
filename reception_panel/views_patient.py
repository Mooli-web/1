# reception_panel/views_patient.py
"""
این فایل شامل تمام ویوهای مربوط به مدیریت بیماران (Patients)
توسط پنل پذیرش است.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q  # برای جستجوی ترکیبی

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
    لیست تمام بیماران همراه با قابلیت جستجو.
    جستجو بر اساس نام، نام خانوادگی، شماره تلفن و نام کاربری انجام می‌شود.
    """
    query = request.GET.get('q', '')
    # پایه کوئری: فقط کاربرانی که نقش "بیمار" دارند
    patients = CustomUser.objects.filter(role=CustomUser.Role.PATIENT).order_by('-date_joined')
    
    if query:
        # استفاده از Q object برای جستجوی OR در چند فیلد
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
    ویو برای ایجاد یک بیمار (کاربر) جدید توسط پذیرش.
    به طور خودکار نقش "PATIENT" و وضعیت "فعال" را تنظیم می‌کند.
    """
    if request.method == 'POST':
        form = ReceptionPatientCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # فرم ReceptionPatientCreationForm نقش را مدیریت می‌کند
            messages.success(request, f"بیمار '{user.username}' با موفقیت ایجاد شد.")
            return redirect('reception_panel:patient_list')
    else:
        form = ReceptionPatientCreationForm()
        
    context = {
        'form': form,
        'title': 'ایجاد بیمار جدید'
    }
    # از تمپلیت patient_form.html برای ایجاد و ویرایش استفاده می‌شود
    return render(request, 'reception_panel/patient_form.html', context)


@staff_required
def patient_detail_view(request, pk):
    """
    نمایش کامل پرونده بیمار در یک صفحه تب-بندی شده.
    این ویو همزمان نمایش اطلاعات (GET) و به‌روزرسانی (POST)
    پروفایل بیمار را مدیریت می‌کند.
    """
    patient = get_object_or_404(CustomUser, pk=pk, role=CustomUser.Role.PATIENT)
    
    if request.method == 'POST':
        # منطق به‌روزرسانی پروفایل بیمار
        u_form = ReceptionPatientUpdateForm(request.POST, instance=patient)
        p_form = ReceptionProfileUpdateForm(request.POST, request.FILES, instance=patient.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f"اطلاعات '{patient.username}' با موفقیت به‌روزرسانی شد.")
            # بازگشت به همین صفحه برای نمایش تغییرات
            return redirect('reception_panel:patient_detail', pk=patient.pk)
    else:
        # آماده‌سازی فرم‌ها برای نمایش در حالت GET
        u_form = ReceptionPatientUpdateForm(instance=patient)
        p_form = ReceptionProfileUpdateForm(instance=patient.profile)

    # واکشی اطلاعات مورد نیاز برای سایر تب‌ها
    patient_appointments = Appointment.objects.filter(patient=patient).prefetch_related('services', 'selected_device').order_by('-start_time')
    patient_transactions = Transaction.objects.filter(appointment__patient=patient).order_by('-created_at')
    patient_consultations = ConsultationRequest.objects.filter(patient=patient).order_by('-created_at')

    context = {
        'patient': patient,
        'u_form': u_form,  # فرم اطلاعات کاربری (User)
        'p_form': p_form,  # فرم اطلاعات پروفایل (Profile)
        'appointments': patient_appointments,
        'transactions': patient_transactions,
        'consultations': patient_consultations,
    }
    return render(request, 'reception_panel/patient_detail.html', context)