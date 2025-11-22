# booking/views.py
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
from site_settings.models import SiteSettings
from .utils import _get_patient_for_booking, _calculate_discounts

@login_required
def create_booking_view(request):
    """
    ویو ایجاد نوبت جدید.
    مدیریت همزمانی: استفاده از select_for_update برای جلوگیری از رزرو تکراری.
    """
    patient_user, is_reception_booking, tmpl_patient = _get_patient_for_booking(request)
    
    if not patient_user: 
        messages.error(request, "کاربر نامعتبر است.")
        return redirect('reception_panel:dashboard')
    
    # دریافت نرخ تبدیل امتیاز
    try:
        points_rate = SiteSettings.load().price_to_points_rate
    except:
        points_rate = 0

    if request.method == 'POST':
        # دریافت داده‌ها
        service_ids = request.POST.getlist('services[]') 
        start_time_str = request.POST.get('slot')
        apply_points = request.POST.get('apply_points') == 'on' # هندل کردن چک‌باکس HTML
        discount_code = request.POST.get('discount_code', '').strip()
        device_id = request.POST.get('device_id')
        manual_confirm = request.POST.get('manual_confirm')

        # اعتبارسنجی اولیه
        if not all([service_ids, start_time_str]):
            messages.error(request, 'لطفا سرویس و زمان را انتخاب کنید.')
            return redirect('booking:create_booking')
        
        selected_services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not selected_services.exists():
            messages.error(request, 'سرویس نامعتبر.')
            return redirect('booking:create_booking')
            
        group = selected_services.first().group
        selected_device = None
        
        if group.has_devices:
            if not device_id:
                messages.error(request, 'انتخاب دستگاه الزامی است.')
                return redirect('booking:create_booking')
            try:
                selected_device = group.available_devices.get(id=device_id)
            except Device.DoesNotExist:
                messages.error(request, 'دستگاه نامعتبر.')
                return redirect('booking:create_booking')
        
        # محاسبات مالی
        total_price = sum(s.price for s in selected_services)
        total_duration = sum(s.duration for s in selected_services)

        p_disc, p_used, c_disc, c_obj, err_msg = _calculate_discounts(
            patient_user, total_price, apply_points, discount_code
        )
        if err_msg:
            messages.warning(request, err_msg) # Warning بجای Error که فرم نپرد

        try:
            aware_start = datetime.fromisoformat(start_time_str)
            aware_end = aware_start + timedelta(minutes=total_duration)
        except ValueError:
            messages.error(request, 'فرمت زمان نامعتبر.')
            return redirect('booking:create_booking')

        # --- تراکنش اتمیک برای جلوگیری از Race Condition ---
        try:
            with transaction.atomic():
                # قفل کردن ردیف‌های مرتبط برای خواندن
                # ما نوبت‌هایی که در این بازه هستند را چک می‌کنیم
                collision_qs = Appointment.objects.select_for_update().filter(
                    start_time__lt=aware_end,
                    end_time__gt=aware_start,
                    status__in=['PENDING', 'CONFIRMED']
                )

                if group.has_devices:
                    if collision_qs.filter(selected_device=selected_device).exists():
                        raise ValueError('این زمان پر شده است.')
                else:
                    if collision_qs.filter(selected_device__isnull=True).exists():
                         raise ValueError('این زمان پر شده است.')

                status = 'CONFIRMED' if (is_reception_booking and manual_confirm) else 'PENDING'

                appt = Appointment.objects.create(
                    patient=patient_user,
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
                
                # کسر امتیاز در صورت استفاده (باید اینجا انجام شود تا اتمیک باشد)
                if p_used > 0:
                    patient_user.profile.points -= p_used
                    patient_user.profile.save()

                if c_obj and c_obj.is_one_time:
                    c_obj.is_used = True
                    c_obj.save()

            # --- پایان تراکنش ---
            
            # ریدایرکت‌ها و نوتیفیکیشن‌ها (خارج از بلوک اتمیک بهتر است)
            if is_reception_booking:
                del request.session['reception_acting_as_patient_id']
                messages.success(request, f"نوبت برای {patient_user.username} ثبت شد.")
                return redirect('reception_panel:dashboard')

            return redirect(reverse('payment:start_payment', args=[appt.id]))

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'خطای سیستمی رخ داد. لطفا مجدد تلاش کنید.')
            print(f"Booking Error: {e}") # Log در پروداکشن

        return redirect('booking:create_booking')

    # GET Request
    context = {
        'groups': ServiceGroup.objects.prefetch_related('services').all(),
        'user_points': patient_user.profile.points,
        'patient_user_for_template': tmpl_patient,
        'price_to_points_rate': points_rate, 
    }
    return render(request, 'booking/create_booking.html', context)

@login_required
def rate_appointment_view(request, appointment_id):
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
            
            messages.success(request, "نظر شما ثبت شد.")
            return redirect('users:dashboard')
    else:
        form = RatingForm()

    return render(request, 'booking/rate_appointment.html', {'form': form, 'appointment': appointment})