# mooli-web/1/1-2999ccca228691e98884cd3ee5f78a1f5e918b61/booking/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from clinic.models import Service, DiscountCode, ServiceGroup, Device, WorkHours, Testimonial
from .models import Appointment
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Q 
from django.views.decorators.http import require_POST
from .forms import RatingForm
from users.models import CustomUser
from reception_panel.models import Notification
import jdatetime 

# --- REFACTOR HELPER 1: Get Patient User ---
def _get_patient_for_booking(request):
    """
    Determines which patient is booking.
    Returns (patient_user, is_reception_booking, patient_user_for_template)
    """
    is_reception_booking = False
    patient_user = request.user
    patient_user_for_template = None

    if request.user.is_staff and request.session.get('reception_acting_as_patient_id'):
        is_reception_booking = True
        try:
            patient_user = CustomUser.objects.get(id=request.session['reception_acting_as_patient_id'])
            patient_user_for_template = patient_user # For template context
        except CustomUser.DoesNotExist:
            patient_user = None # Will be caught later
    
    return patient_user, is_reception_booking, patient_user_for_template

# --- REFACTOR HELPER 2: Calculate Discounts ---
def _calculate_discounts(patient_user, total_price, apply_points_str, discount_code_str):
    """
    Calculates points and code discounts.
    Returns (points_discount, points_to_use, code_discount, discount_code_obj, error_message)
    """
    points_discount = 0
    points_to_use = 0
    code_discount = 0
    discount_code_obj = None
    error_message = None

    # 1. Calculate points discount
    if apply_points_str:
        profile = patient_user.profile
        max_possible_discount = profile.points * settings.POINTS_TO_TOMAN_RATE
        points_discount = min(max_possible_discount, total_price) 
        points_to_use = int(points_discount / settings.POINTS_TO_TOMAN_RATE)

    # 2. Calculate code discount
    if discount_code_str:
        try:
            discount_code_obj = DiscountCode.objects.get(code__iexact=discount_code_str)
            if not discount_code_obj.is_valid():
                error_message = 'کد تخفیف معتبر نیست یا منقضی شده.'
                discount_code_obj = None
            elif discount_code_obj.user and discount_code_obj.user != patient_user:
                error_message = 'این کد تخفیف مخصوص شما نیست.'
                discount_code_obj = None
            elif discount_code_obj.is_one_time and discount_code_obj.is_used:
                error_message = 'این کد تخفیف قبلاً استفاده شده است.'
                discount_code_obj = None
            else:
                if discount_code_obj.discount_type == 'PERCENTAGE':
                    code_discount = (total_price * discount_code_obj.value) / 100
                else: # FIXED_AMOUNT
                    code_discount = discount_code_obj.value
        except DiscountCode.DoesNotExist:
            error_message = 'کد تخفیف یافت نشد.'
            discount_code_obj = None # Ensure it's None

    return points_discount, points_to_use, code_discount, discount_code_obj, error_message


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

def get_services_for_group_api(request):
    group_id = request.GET.get('group_id')
    if not group_id:
        return JsonResponse({'error': 'Missing group_id'}, status=400)
    try:
        group = ServiceGroup.objects.prefetch_related('available_devices').get(id=group_id)
        services = group.services.all()
        
        data = {
            'allow_multiple_selection': group.allow_multiple_selection,
            'has_devices': group.has_devices,
            'devices': [
                {'id': d.id, 'name': d.name} for d in group.available_devices.all()
            ],
            'services': [
                {
                    'id': service.id,
                    'name': service.name,
                    'price': service.price,
                    'duration': service.duration,
                }
                for service in services
            ]
        }
        return JsonResponse(data)
    except ServiceGroup.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)

# ***
# *** API دریافت اسلات‌ها (اصلاح شده) ***
# ***
def get_available_slots_api(request):
    date_str = request.GET.get('date')
    service_ids = request.GET.getlist('service_ids[]')
    
    # *** دریافت شناسه دستگاه از درخواست ***
    device_id = request.GET.get('device_id') # می‌تواند خالی ("") باشد

    try:
        total_duration = int(request.GET.get('total_duration', 30))
    except ValueError:
        total_duration = 30
        
    if not date_str or total_duration == 0 or not service_ids:
        return JsonResponse({'error': 'Missing or invalid parameters'}, status=400)
    
    patient_user = request.user
    if request.user.is_staff and request.session.get('reception_acting_as_patient_id'):
        try:
            patient_user = CustomUser.objects.get(id=request.session['reception_acting_as_patient_id'])
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=400)
    
    user_gender = patient_user.gender
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not services.exists():
            return JsonResponse({'error': 'Invalid services'}, status=400)
        
        # *** بررسی نیاز به دستگاه ***
        service = services.first() 
        service_group = service.group
        
        # اگر گروه دستگاه لازم دارد اما دستگاهی (device_id) انتخاب نشده، خطا برگردان
        if service_group.has_devices and not device_id:
             return JsonResponse({'error': 'برای این خدمت انتخاب دستگاه الزامی است.'}, status=400)
             
    except (ValueError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    day_of_week_python = selected_date.weekday()
    our_day_of_week = (day_of_week_python + 2) % 7 

    if user_gender:
        gender_filter = Q(gender_specific=user_gender) | Q(gender_specific='ALL')
    else:
        gender_filter = Q(gender_specific='ALL')
    
    work_hours_list = service.work_hours.filter(
        day_of_week=our_day_of_week
    ).filter(gender_filter)
    
    if not work_hours_list.exists():
        work_hours_list = service.group.work_hours.filter(
            day_of_week=our_day_of_week
        ).filter(gender_filter)

    if not work_hours_list.exists():
        return JsonResponse({'available_slots': []}) # روز تعطیل

    start_of_day = timezone.make_aware(datetime.combine(selected_date, time.min))
    end_of_day = timezone.make_aware(datetime.combine(selected_date, time.max))
    
    # *** اصلاح کوئری نوبت‌های رزرو شده بر اساس دستگاه ***
    appointments_query = Appointment.objects.filter(
        start_time__range=(start_of_day, end_of_day),
        status__in=['CONFIRMED', 'PENDING']
    )

    if service_group.has_devices:
        # این گروه دستگاه دارد، فقط نوبت‌های همان دستگاه را بگیر
        booked_appointments = appointments_query.filter(selected_device_id=device_id)
    else:
        # این گروه دستگاه ندارد، فقط نوبت‌های بدون دستگاه را بگیر
        booked_appointments = appointments_query.filter(selected_device__isnull=True)
    
    current_tz = timezone.get_current_timezone()
    booked_intervals = []
    for app in booked_appointments:
        booked_intervals.append(
            (timezone.localtime(app.start_time, current_tz),
             timezone.localtime(app.end_time, current_tz))
        )

    available_slots = []
    
    for workday in work_hours_list:
        workday_start, workday_end = workday.start_time, workday.end_time
        
        current_time_dt = datetime.combine(selected_date, workday_start)
        end_time_dt = datetime.combine(selected_date, workday_end)

        while current_time_dt < end_time_dt:
            potential_start_aware = timezone.make_aware(current_time_dt)
            potential_end_aware = potential_start_aware + timedelta(minutes=total_duration)

            if potential_start_aware > timezone.now():
                if potential_end_aware.time() <= workday_end:
                    is_overlapping = False
                    for start, end in booked_intervals:
                        if (potential_start_aware < end and potential_end_aware > start):
                            is_overlapping = True
                            break
                    
                    if not is_overlapping:
                        available_slots.append(current_time_dt.strftime('%H:%M'))
            
            # *** مهم: این بخش در فایل اصلی شما اشتباه بود ***
            # افزایش زمان باید بر اساس *مدت زمان سرویس* باشد، نه یک مقدار ثابت
            if total_duration > 0:
                 current_time_dt += timedelta(minutes=total_duration)
            else:
                 current_time_dt += timedelta(minutes=30) # یک پیش‌فرض امن

    return JsonResponse({'available_slots': available_slots})


@require_POST
@login_required
def apply_discount_api(request):
    # (این تابع بدون تغییر است)
    code = request.POST.get('code', '').strip()
    total_price_str = request.POST.get('total_price', '0')
    
    patient_user = request.user
    if request.user.is_staff and request.session.get('reception_acting_as_patient_id'):
        try:
            patient_user = CustomUser.objects.get(id=request.session['reception_acting_as_patient_id'])
        except CustomUser.DoesNotExist:
             return JsonResponse({'status': 'error', 'message': 'بیمار یافت نشد.'}, status=404)

    try:
        total_price = float(total_price_str)
    except ValueError:
        total_price = 0

    if not code or total_price == 0:
        return JsonResponse({'status': 'error', 'message': 'کد یا مبلغ نامعتبر است.'}, status=400)

    try:
        discount_code = DiscountCode.objects.get(code__iexact=code)

        if not discount_code.is_valid():
            return JsonResponse({'status': 'error', 'message': 'کد تخفیف معتبر نیست یا منقضی شده.'}, status=400)
            
        if discount_code.user and discount_code.user != patient_user:
            return JsonResponse({'status': 'error', 'message': 'این کد تخفیف مخصوص شما نیست.'}, status=400)
            
        if discount_code.is_one_time and discount_code.is_used:
             return JsonResponse({'status': 'error', 'message': 'این کد تخفیف قبلاً استفاده شده است.'}, status=400)

        discount_amount = 0
        if discount_code.discount_type == 'PERCENTAGE':
            discount_amount = (total_price * discount_code.value) / 100
        else: # FIXED_AMOUNT
            discount_amount = discount_code.value

        return JsonResponse({'status': 'success', 'discount_amount': discount_amount})

    except DiscountCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'کد تخفیف یافت نشد.'}, status=404)


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


# ***
# *** تابع کمکی (اصلاح شده) ***
# ***
def get_available_slots_for_day(selected_date, total_duration, service_ids, patient_user, device_id):
    """
    (تابع کمکی) بررسی می‌کند که آیا در یک روز خاص، حداقل یک اسلات خالی وجود دارد یا خیر.
    پارامتر device_id به آن اضافه شده است.
    """
    
    user_gender = patient_user.gender
    if user_gender:
        gender_filter = Q(gender_specific=user_gender) | Q(gender_specific='ALL')
    else:
        gender_filter = Q(gender_specific='ALL')

    try:
        services = Service.objects.select_related('group').filter(id__in=service_ids)
        if not services.exists():
            return 'unavailable' 
        service = services.first()
        service_group = service.group 
        
        # *** بررسی نیاز به دستگاه در تابع کمکی ***
        if service_group.has_devices and not device_id:
            return 'unavailable' # نمی‌توان در دسترس بودن را بدون دستگاه چک کرد

        our_day_of_week = (selected_date.weekday() + 2) % 7 
        
        work_hours_list = service.work_hours.filter(
            day_of_week=our_day_of_week
        ).filter(gender_filter)
        
        if not work_hours_list.exists():
            work_hours_list = service.group.work_hours.filter(
                day_of_week=our_day_of_week
            ).filter(gender_filter)

        if not work_hours_list.exists():
            return 'unavailable' 
            
    except Exception:
        return 'unavailable'

    start_of_day = timezone.make_aware(datetime.combine(selected_date, time.min))
    end_of_day = timezone.make_aware(datetime.combine(selected_date, time.max))
    
    # *** اصلاح کوئری نوبت‌های رزرو شده در تابع کمکی ***
    appointments_query = Appointment.objects.filter(
        start_time__range=(start_of_day, end_of_day),
        status__in=['CONFIRMED', 'PENDING']
    )

    if service_group.has_devices:
        booked_appointments = appointments_query.filter(selected_device_id=device_id)
    else:
        booked_appointments = appointments_query.filter(selected_device__isnull=True)
    
    current_tz = timezone.get_current_timezone()
    booked_intervals = []
    for app in booked_appointments:
        booked_intervals.append(
            (timezone.localtime(app.start_time, current_tz),
             timezone.localtime(app.end_time, current_tz))
        )

    for workday in work_hours_list:
        workday_start, workday_end = workday.start_time, workday.end_time
        current_time_dt = datetime.combine(selected_date, workday_start)
        end_time_dt = datetime.combine(selected_date, workday_end)

        while current_time_dt < end_time_dt:
            potential_start_aware = timezone.make_aware(current_time_dt)
            potential_end_aware = potential_start_aware + timedelta(minutes=total_duration)

            if potential_start_aware > timezone.now(): 
                if potential_end_aware.time() <= workday_end: 
                    is_overlapping = False
                    for start, end in booked_intervals:
                        if (potential_start_aware < end and potential_end_aware > start):
                            is_overlapping = True
                            break
                    
                    if not is_overlapping:
                        return 'available'
            
            if total_duration > 0:
                 current_time_dt += timedelta(minutes=total_duration)
            else:
                 current_time_dt += timedelta(minutes=30)

    return 'full'


# ***
# *** API دریافت وضعیت ماه (اصلاح شده) ***
# ***
def get_month_availability_api(request):
    """
    API جدید برای بررسی وضعیت تمام روزهای یک ماه.
    (اصلاح شده برای دریافت و ارسال device_id)
    """
    service_ids = request.GET.getlist('service_ids[]')
    try:
        total_duration = int(request.GET.get('total_duration', 30))
    except ValueError:
        total_duration = 30
    
    # *** دریافت شناسه دستگاه ***
    device_id = request.GET.get('device_id')
    
    try:
        j_year = int(request.GET.get('year'))
        j_month = int(request.GET.get('month'))
    except (TypeError, ValueError):
        today = jdatetime.date.today()
        j_year, j_month = today.year, today.month

    if total_duration == 0 or not service_ids:
        return JsonResponse({'error': 'Missing or invalid parameters'}, status=400)

    patient_user = request.user
    if request.user.is_staff and request.session.get('reception_acting_as_patient_id'):
        try:
            patient_user = CustomUser.objects.get(id=request.session['reception_acting_as_patient_id'])
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=400)
    
    availability_data = {}
    
    if j_month == 12:
        days_in_month = 29 
    elif j_month <= 6:
        days_in_month = 31
    else:
        days_in_month = 30

    gregorian_today = datetime.today().date()

    for day in range(1, days_in_month + 1):
        try:
            j_date_str = f"{j_year}-{j_month}-{day}"
            j_date = jdatetime.date(j_year, j_month, day)
            g_date = j_date.togregorian()
            
            if g_date < gregorian_today:
                availability_data[j_date_str] = 'past'
            else:
                # *** ارسال شناسه دستگاه به تابع کمکی ***
                status = get_available_slots_for_day(g_date, total_duration, service_ids, patient_user, device_id)
                availability_data[j_date_str] = status
        
        except ValueError:
            pass 

    return JsonResponse(availability_data)