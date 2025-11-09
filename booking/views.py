# booking/views.py
# فایل اصلاح‌شده: این فایل فقط شامل ویوهای رندرکننده HTML است.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta

from clinic.models import Service, ServiceGroup, Device, Testimonial
from .models import Appointment
from .forms import RatingForm
from users.models import CustomUser
from reception_panel.models import Notification

# توابع کمکی را از utils.py وارد می‌کنیم
from .utils import _get_patient_for_booking, _calculate_discounts


@login_required
def create_booking_view(request):
    
    patient_user, is_reception_booking, patient_user_for_template = _get_patient_for_booking(request)
    
    if patient_user is None: 
        messages.error(request, "بیمار انتخاب شده یافت نشد.")
        if 'reception_acting_as_patient_id' in request.session:
            del request.session['reception_acting_as_patient_id']
        return redirect('reception_panel:dashboard')
    
    initial_user_points = patient_user.profile.points
    initial_max_discount = initial_user_points * settings.POINTS_TO_TOMAN_RATE

    if request.method == 'POST':
        # --- 1. Get data from POST ---
        service_ids = request.POST.getlist('services[]') 
        start_time_str = request.POST.get('slot')
        apply_points_str = request.POST.get('apply_points')
        discount_code_str = request.POST.get('discount_code', '').strip()
        device_id = request.POST.get('device_id')
        manual_confirm_str = request.POST.get('manual_confirm')

        if not all([service_ids, start_time_str]):
            messages.error(request, 'اطلاعات ارسالی ناقص است. (خدمت یا زمان انتخاب نشده)')
            return redirect('booking:create_booking')
        
        # --- 2. Validate Services and Device ---
        selected_services = Service.objects.filter(id__in=service_ids)
        if not selected_services.exists():
            messages.error(request, 'خدمات انتخاب شده نامعتبر هستند.')
            return redirect('booking:create_booking')
            
        selected_device = None
        service_group = selected_services.first().group
        
        if service_group.has_devices:
            if not device_id:
                messages.error(request, 'لطفاً دستگاه مورد نظر را انتخاب کنید.')
                return redirect('booking:create_booking')
            try:
                selected_device = service_group.available_devices.get(id=device_id)
            except Device.DoesNotExist:
                messages.error(request, 'دستگاه انتخاب شده نامعتبر است.')
                return redirect('booking:create_booking')
        
        total_price = sum(s.price for s in selected_services)
        total_duration = sum(s.duration for s in selected_services)

        # --- 3. REFACTOR: Use helper to calculate discounts ---
        points_discount, points_to_use, code_discount, discount_code_obj, error_message = _calculate_discounts(
            patient_user, total_price, apply_points_str, discount_code_str
        )
        
        if error_message:
            messages.error(request, error_message)

        total_discount = min(points_discount + code_discount, total_price)

        # --- 4. Validate Time and Check Overlap ---
        try:
            naive_start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
            aware_start_time = timezone.make_aware(naive_start_time)
            aware_end_time = aware_start_time + timedelta(minutes=total_duration)
        except ValueError:
            messages.error(request, 'فرمت زمان ارسالی نامعتبر است.')
            return redirect('booking:create_booking')

        try:
            with transaction.atomic():
                # *** راه‌حل مشکل اصلی (منطق بک‌اند): اصلاح منطق بررسی تداخل ***
                appointments_query = Appointment.objects.select_for_update().filter(
                    start_time__lt=aware_end_time,
                    end_time__gt=aware_start_time,
                    status__in=['PENDING', 'CONFIRMED']
                )

                if service_group.has_devices:
                    # اگر این گروه دستگاه دارد، فقط نوبت‌هایی که *همین دستگاه* را رزرو کرده‌اند بررسی کن
                    overlapping_appointments = appointments_query.filter(selected_device=selected_device).exists()
                else:
                    # اگر این گروه دستگاه ندارد، فقط نوبت‌هایی که *بدون دستگاه* رزرو شده‌اند بررسی کن
                    overlapping_appointments = appointments_query.filter(selected_device__isnull=True).exists()
                # *** پایان اصلاحیه ***

                if overlapping_appointments:
                    messages.error(request, 'متاسفانه این بازه زمانی با نوبت دیگری تداخل دارد.')
                    return redirect('booking:create_booking')

                status = 'PENDING'
                if is_reception_booking and manual_confirm_str:
                    status = 'CONFIRMED'

                # --- 6. Create Appointment ---
                new_appointment = Appointment.objects.create(
                    patient=patient_user,
                    start_time=aware_start_time,
                    end_time=aware_end_time,
                    status=status,
                    points_discount_amount=points_discount,
                    points_used=points_to_use, 
                    discount_code=discount_code_obj, 
                    code_discount_amount=code_discount,
                    selected_device=selected_device,
                )
                
                new_appointment.services.set(selected_services)
            
            # --- 7. Redirect based on flow ---
            if is_reception_booking:
                if 'reception_acting_as_patient_id' in request.session:
                    del request.session['reception_acting_as_patient_id']
                
                if status == 'CONFIRMED': # Manually confirmed
                    messages.success(request, f"نوبت برای {patient_user.username} با موفقیت (به صورت دستی) ثبت شد.")
                    
                    staff_users = CustomUser.objects.filter(is_staff=True)
                    notification_link = request.build_absolute_uri(reverse('reception_panel:appointment_list'))
                    for staff in staff_users:
                        Notification.objects.create(
                            user=staff,
                            message=f"نوبت دستی جدید برای {patient_user.username} ثبت شد.",
                            link=notification_link
                        )
                    return redirect('reception_panel:dashboard')
                else:
                    return redirect(reverse('payment:start_payment', args=[new_appointment.id]))

            return redirect(reverse('payment:start_payment', args=[new_appointment.id]))

        except Exception as e:
            messages.error(request, f'خطایی در فرآیند رزرو رخ داد: {e}')
            pass 

    # --- GET Request ---
    groups = ServiceGroup.objects.all()
    context = {
        'groups': groups,
        'user_points': initial_user_points,
        'max_discount': initial_max_discount,
        'patient_user_for_template': patient_user_for_template,
    }
    return render(request, 'booking/create_booking.html', context)


@login_required
def rate_appointment_view(request, appointment_id):
    # (این تابع بدون تغییر است)
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user,
        status='DONE',
        is_rated=False
    )
    
    first_service = appointment.services.first()
    if not first_service:
        messages.error(request, "نوبت مورد نظر خدمتی برای امتیازدهی ندارد.")
        return redirect('users:dashboard')

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                testimonial = form.save(commit=False)
                testimonial.patient_name = request.user.get_full_name() or request.user.username
                testimonial.service = first_service 
                testimonial.save()
                
                staff_users = CustomUser.objects.filter(is_staff=True)
                notification_link = request.build_absolute_uri(
                    reverse('reception_panel:dashboard') 
                )
                for staff in staff_users:
                    Notification.objects.create(
                        user=staff,
                        message=f"نظر جدیدی توسط {request.user.username} برای نوبت {appointment.id} ثبت شد.",
                        link=notification_link
                    )

                appointment.is_rated = True
                appointment.save()
            
            messages.success(request, "نظر شما با موفقیت ثبت شد. متشکریم!")
            return redirect('users:dashboard')
    else:
        form = RatingForm()

    context = {
        'form': form,
        'appointment': appointment
    }
    return render(request, 'booking/rate_appointment.html', context)