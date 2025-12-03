# booking/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta

from clinic.models import Service, ServiceGroup, Device
from .models import Appointment
from .forms import RatingForm
from site_settings.models import SiteSettings
from .utils import _get_patient_for_booking, _calculate_discounts

def create_booking_view(request):
    """
    ویو ایجاد نوبت جدید.
    پشتیبانی از کاربران مهمان (بدون لاگین) و کاربران عضو.
    """
    patient_user, is_reception_booking, tmpl_patient = _get_patient_for_booking(request)
    
    # محاسبه امتیاز کاربر (فقط اگر کاربر لاگین باشد)
    user_points = 0
    if patient_user:
        try:
            user_points = patient_user.profile.points
        except:
            pass

    try:
        settings_obj = SiteSettings.load()
        points_rate = settings_obj.price_to_points_rate
    except:
        points_rate = 0

    if request.method == 'POST':
        # --- دریافت داده‌ها ---
        service_ids = request.POST.getlist('services[]') 
        start_time_str = request.POST.get('slot')
        apply_points = request.POST.get('apply_points') == 'on'
        discount_code = request.POST.get('discount_code', '').strip()
        device_id = request.POST.get('device_id')
        manual_confirm = request.POST.get('manual_confirm')
        
        # دریافت اطلاعات مهمان
        guest_fname = request.POST.get('guest_first_name')
        guest_lname = request.POST.get('guest_last_name')
        guest_phone = request.POST.get('guest_phone')

        # --- اعتبارسنجی اولیه ---
        if not all([service_ids, start_time_str]):
            messages.error(request, 'لطفا سرویس و زمان را انتخاب کنید.')
            return redirect('booking:create_booking')
        
        # اگر کاربر لاگین نیست، اطلاعات مهمان اجباری است
        if not patient_user:
            if not all([guest_fname, guest_lname, guest_phone]):
                messages.error(request, 'لطفا نام و شماره تماس خود را وارد کنید.')
                return redirect('booking:create_booking')

        selected_services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not selected_services.exists():
            messages.error(request, 'سرویس انتخابی نامعتبر است.')
            return redirect('booking:create_booking')
            
        group = selected_services.first().group
        selected_device = None
        
        # اعتبارسنجی دستگاه
        if group.has_devices:
            if not device_id:
                messages.error(request, 'انتخاب دستگاه الزامی است.')
                return redirect('booking:create_booking')
            try:
                selected_device = group.available_devices.get(id=device_id)
            except Device.DoesNotExist:
                messages.error(request, 'دستگاه نامعتبر است.')
                return redirect('booking:create_booking')
        
        # --- محاسبات مالی ---
        total_price = sum(s.price for s in selected_services)
        total_duration = sum(s.duration for s in selected_services)

        p_disc, p_used, c_disc, c_obj, err_msg = _calculate_discounts(
            patient_user, total_price, apply_points, discount_code
        )
        
        if err_msg:
            messages.warning(request, err_msg)

        try:
            aware_start = datetime.fromisoformat(start_time_str)
            aware_end = aware_start + timedelta(minutes=total_duration)
            
            # جلوگیری از رزرو در گذشته
            if aware_start < timezone.now():
                raise ValueError('زمان انتخاب شده منقضی شده است.')
                
        except ValueError:
            messages.error(request, 'فرمت زمان یا تاریخ نامعتبر است.')
            return redirect('booking:create_booking')

        # --- تراکنش اتمیک و قفل رکورد ---
        try:
            with transaction.atomic():
                # بررسی تداخل زمانی
                collision_qs = Appointment.objects.select_for_update().filter(
                    start_time__lt=aware_end,
                    end_time__gt=aware_start,
                    status__in=['PENDING', 'CONFIRMED']
                )

                if group.has_devices:
                    if collision_qs.filter(selected_device=selected_device).exists():
                        raise ValueError('متاسفانه این زمان پر شد.')
                else:
                    if collision_qs.filter(selected_device__isnull=True).exists():
                         raise ValueError('متاسفانه این زمان پر شده است.')

                status = 'CONFIRMED' if (is_reception_booking and manual_confirm) else 'PENDING'

                # ایجاد نوبت (با یا بدون کاربر)
                appt = Appointment.objects.create(
                    patient=patient_user, # ممکن است None باشد
                    guest_first_name=guest_fname,
                    guest_last_name=guest_lname,
                    guest_phone_number=guest_phone,
                    start_time=aware_start,
                    end_time=aware_end,
                    status=status,
                    points_discount_amount=p_disc,
                    points_used=p_used, 
                    discount_code=c_obj, 
                    code_discount_amount=c_disc,
                    selected_device=selected_device,
                )
                appt.services.set(selected_services)
                
                # کسر امتیاز (فقط اگر کاربر باشد و امتیاز استفاده کرده باشد)
                if patient_user and p_used > 0:
                    patient_user.profile.points -= p_used
                    patient_user.profile.save()

                # مصرف کد تخفیف یکبار مصرف
                if c_obj and c_obj.is_one_time:
                    c_obj.is_used = True
                    c_obj.save()

            # --- پایان تراکنش ---
            
            if is_reception_booking:
                if 'reception_acting_as_patient_id' in request.session:
                    del request.session['reception_acting_as_patient_id']
                
                name = patient_user.get_full_name() if patient_user else f"{guest_fname} {guest_lname}"
                messages.success(request, f"نوبت برای {name} با موفقیت ثبت شد. کد رهگیری: {appt.tracking_code}")
                return redirect('reception_panel:dashboard')

            return redirect(reverse('payment:start_payment', args=[appt.id]))

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            print(f"Booking System Error: {e}")
            messages.error(request, 'خطای سیستمی رخ داد. لطفا مجدد تلاش کنید.')

        return redirect('booking:create_booking')

    # --- GET Request ---
    groups = ServiceGroup.objects.prefetch_related('services').all()
    suggested_service = Service.objects.filter(price__lte=500000).first()

    context = {
        'groups': groups,
        'user_points': user_points, # برای مهمان 0 است
        'patient_user_for_template': tmpl_patient,
        'price_to_points_rate': points_rate,
        'today_date_server': timezone.now().strftime("%Y-%m-%d"),
        'suggested_service': suggested_service,
        'is_guest': patient_user is None # پرچم برای نمایش فرم مهمان در فرانت
    }
    return render(request, 'booking/create_booking.html', context)

@login_required
def rate_appointment_view(request, appointment_id):
    """ثبت نظر برای نوبت انجام شده (فقط برای کاربران عضو)."""
    appointment = get_object_or_404(
        Appointment.objects.prefetch_related('services'),
        id=appointment_id,
        patient=request.user,
        status='DONE',
        is_rated=False
    )
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.patient_name = request.user.get_full_name() or request.user.username
            testimonial.service = appointment.services.first()
            testimonial.save()
            
            appointment.is_rated = True
            appointment.save(update_fields=['is_rated'])
            
            messages.success(request, "نظر شما با موفقیت ثبت شد. با تشکر از بازخورد شما.")
            return redirect('users:dashboard')
    else:
        form = RatingForm()

    return render(request, 'booking/rate_appointment.html', {'form': form, 'appointment': appointment})