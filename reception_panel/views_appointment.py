# reception_panel/views_appointment.py
"""
این فایل شامل تمام ویوهای مربوط به مدیریت نوبت‌ها (Appointments)
و فرآیند رزرو دستی توسط پذیرش است.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST

from .decorators import staff_required
from users.models import CustomUser
from booking.models import Appointment


# --- ویوهای رزرو دستی (Manual Booking) ---

@staff_required
def booking_select_patient_view(request):
    """
    مرحله اول رزرو دستی: انتخاب بیمار.
    پذیرش، بیماری که می‌خواهد برای او نوبت ثبت کند را جستجو و انتخاب می‌کند.
    """
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
    """
    مرحله دوم رزرو دستی: شبیه‌سازی بیمار.
    ID بیمار انتخاب شده در سشن (session) کاربر پذیرش ذخیره می‌شود.
    سپس پذیرش به صفحه رزرو عمومی (booking:create_booking) هدایت می‌شود.
    ویو create_booking چک می‌کند که آیا این ID در سشن وجود دارد یا خیر.
    """
    patient = get_object_or_404(CustomUser, id=patient_id, role=CustomUser.Role.PATIENT)
    # ذخیره ID بیمار در سشن برای استفاده در ویو رزرو
    request.session['reception_acting_as_patient_id'] = patient.id
    return redirect('booking:create_booking')

# --- ویوهای مدیریت لیست نوبت‌ها ---

@staff_required
def appointment_list_view(request):
    """
    نمایش لیست کامل تمام نوبت‌های ثبت شده در سیستم.
    از prefetch_related برای بهینه‌سازی کوئری خدمات (M2M) استفاده شده است.
    """
    appointments = Appointment.objects.prefetch_related(
        'services', 'patient', 'selected_device'
    ).order_by('-start_time')
    
    context = {
        'appointments': appointments
    }
    return render(request, 'reception_panel/appointment_list.html', context)

# --- ویوهای عملیاتی (Actions) ---

@staff_required
@require_POST # اطمینان از اینکه این ویو فقط با متد POST فراخوانی می‌شود
def cancel_appointment_view(request, pk):
    """
    عملیات لغو کردن یک نوبت (توسط پذیرش).
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # فقط نوبت‌هایی که در انتظار یا تایید شده هستند قابل لغو می‌باشند
    if appointment.status in ['PENDING', 'CONFIRMED']:
        appointment.status = 'CANCELED'
        appointment.save()
        messages.success(request, f"نوبت شماره {appointment.pk} با موفقیت لغو شد.")
        # در اینجا می‌توان منطق بازگشت امتیاز یا وجه را اضافه کرد
    else:
        messages.error(request, "این نوبت در وضعیتی نیست که بتوان آن را لغو کرد.")
    
    # بازگشت به صفحه‌ای که کاربر از آن آمده (مثلاً لیست نوبت‌ها یا پروفایل بیمار)
    return redirect(request.META.get('HTTP_REFERER', 'reception_panel:appointment_list'))

@staff_required
@require_POST
def mark_appointment_done_view(request, pk):
    """
    عملیات "انجام شد" برای یک نوبت (توسط پذیرش).
    """
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # فقط نوبت‌های "تایید شده" را می‌توان "انجام شده" علامت زد
    if appointment.status == 'CONFIRMED':
        appointment.status = 'DONE'
        appointment.save()
        messages.success(request, f"نوبت شماره {appointment.pk} به 'انجام شده' تغییر یافت.")
        # طبق تعریف، نوبت‌هایی که دستی "انجام" می‌شوند امتیازی دریافت نمی‌کنند
    else:
        messages.error(request, "فقط نوبت‌های 'تایید شده' را می‌توان 'انجام شده' علامت زد.")
        
    return redirect(request.META.get('HTTP_REFERER', 'reception_panel:appointment_list'))