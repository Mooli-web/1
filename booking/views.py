# booking/views.py
"""
این فایل شامل ویوهای اصلی اپلیکیشن booking است که توسط
کاربر نهایی (بیمار) یا (پذیرش در حال شبیه‌سازی بیمار) استفاده می‌شود.

- create_booking_view: ویو اصلی ایجاد نوبت (هم GET و هم POST).
- rate_appointment_view: ویو ثبت نظر (امتیازدهی) برای نوبت‌های انجام شده.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.db import transaction  # برای قفل کردن دیتابیس هنگام بررسی تداخل
from django.utils import timezone
from datetime import datetime, timedelta
import jdatetime # <-- *** اطمینان از ایمپورت ***

from clinic.models import Service, ServiceGroup, Device, Testimonial
from .models import Appointment
from .forms import RatingForm
from users.models import CustomUser
from reception_panel.models import Notification

# توابع کمکی (Helpers) از utils.py وارد می‌شوند
from .utils import _get_patient_for_booking, _calculate_discounts


@login_required
def create_booking_view(request):
    """
    ویو اصلی و محوری برای ایجاد رزرو جدید.
    این ویو منطق پیچیده‌ای دارد:
    1. (GET): نمایش فرم انتخاب گروه خدمت.
    2. (GET/POST): تشخیص می‌دهد که آیا "پذیرش" در حال رزرو برای "بیمار" است یا خیر.
    3. (POST): اعتبارسنجی تمام داده‌های فرم (خدمات، دستگاه، زمان، تخفیف).
    4. (POST): بررسی تداخل زمانی (Overlapping) با استفاده از transaction.atomic.
    5. (POST): ایجاد نوبت (Appointment) و هدایت به صفحه پرداخت یا داشبورد پذیرش.
    """
    
    # --- تشخیص هویت رزرو کننده ---
    # تابع کمکی _get_patient_for_booking مشخص می‌کند چه کسی در حال رزرو است
    patient_user, is_reception_booking, patient_user_for_template = _get_patient_for_booking(request)
    
    if patient_user is None: 
        # اگر پذیرش بیماری را انتخاب کرده بود اما بیمار یافت نشد
        messages.error(request, "بیمار انتخاب شده یافت نشد.")
        if 'reception_acting_as_patient_id' in request.session:
            del request.session['reception_acting_as_patient_id']
        return redirect('reception_panel:dashboard')
    
    # واکشی اطلاعات اولیه بیمار (برای نمایش امتیاز و تخفیف)
    initial_user_points = patient_user.profile.points
    initial_max_discount = initial_user_points * settings.POINTS_TO_TOMAN_RATE

    if request.method == 'POST':
        # --- منطق POST: پردازش فرم رزرو ---
        
        # --- ۱. خواندن داده‌ها از فرم POST ---
        service_ids = request.POST.getlist('services[]') 
        start_time_str = request.POST.get('slot')
        apply_points_str = request.POST.get('apply_points')
        discount_code_str = request.POST.get('discount_code', '').strip()
        device_id = request.POST.get('device_id')
        manual_confirm_str = request.POST.get('manual_confirm') # مخصوص پذیرش

        # (کد دیباگ حذف شد)

        if not all([service_ids, start_time_str]):
            messages.error(request, 'اطلاعات ارسالی ناقص است. (خدمت یا زمان انتخاب نشده)')
            return redirect('booking:create_booking')
        
        # --- ۲. اعتبارسنجی خدمات و دستگاه ---
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
                # اطمینان از اینکه دستگاه انتخاب شده جزو دستگاه‌های مجاز گروه است
                selected_device = service_group.available_devices.get(id=device_id)
            except Device.DoesNotExist:
                messages.error(request, 'دستگاه انتخاب شده نامعتبر است.')
                return redirect('booking:create_booking')
        
        total_price = sum(s.price for s in selected_services)
        total_duration = sum(s.duration for s in selected_services)

        # --- ۳. محاسبه تخفیف‌ها (با تابع کمکی) ---
        points_discount, points_to_use, code_discount, discount_code_obj, error_message = _calculate_discounts(
            patient_user, total_price, apply_points_str, discount_code_str
        )
        
        if error_message:
            messages.error(request, error_message)
        # مبلغ نهایی تخفیف نمی‌تواند از قیمت کل بیشتر باشد
        total_discount = min(points_discount + code_discount, total_price)

        # --- ۴. اعتبارسنجی زمان و بررسی تداخل ---
        try:
            # ==========================================================
            # --- *** شروع اصلاحیه (حل مشکل فرمت زمان) *** ---
            #
            # فرمت ارسالی از JS یک رشته کامل ISO است 
            # (e.g., '2025-11-18T15:30:00+03:30')
            # از datetime.fromisoformat برای پارس کردن آن استفاده می‌کنیم.
            aware_start_time = datetime.fromisoformat(start_time_str)
            
            # (دیگر نیازی به timezone.make_aware نیست چون زمان ارسالی 'aware' است)
            
            aware_end_time = aware_start_time + timedelta(minutes=total_duration)
            # --- *** پایان اصلاحیه *** ---
            # ==========================================================

        except ValueError:
            messages.error(request, 'فرمت زمان ارسالی نامعتبر است.')
            return redirect('booking:create_booking')

        try:
            # استفاده از transaction.atomic و select_for_update برای جلوگیری از
            # رزرو همزمان (Race Condition)
            with transaction.atomic():
                # --- منطق حیاتی بررسی تداخل ---
                # تمام نوبت‌هایی که با بازه زمانی ما (شروع تا پایان) تداخل دارند
                # و در وضعیت "قطعی" (تایید شده یا در انتظار پرداخت) هستند را قفل کن.
                appointments_query = Appointment.objects.select_for_update().filter(
                    start_time__lt=aware_end_time,  # شروعش قبل از پایان ما باشد
                    end_time__gt=aware_start_time,  # پایانش بعد از شروع ما باشد
                    status__in=['PENDING', 'CONFIRMED']
                )

                # بررسی تداخل بر اساس دستگاه
                if service_group.has_devices:
                    # اگر سرویس ما دستگاهی است، فقط با نوبت‌های "همین دستگاه" تداخل دارد
                    overlapping_appointments = appointments_query.filter(selected_device=selected_device).exists()
                else:
                    # اگر سرویس ما دستگاهی نیست، فقط با نوبت‌های "بدون دستگاه" تداخل دارد
                    overlapping_appointments = appointments_query.filter(selected_device__isnull=True).exists()
                
                if overlapping_appointments:
                    messages.error(request, 'متاسفانه این بازه زمانی لحظاتی پیش توسط شخص دیگری رزرو شد.')
                    return redirect('booking:create_booking')

                # --- ۵. تعیین وضعیت نهایی نوبت ---
                status = 'PENDING'  # پیش‌فرض: در انتظار پرداخت
                if is_reception_booking and manual_confirm_str:
                    status = 'CONFIRMED'  # اگر پذیرش دستی تایید کند

                # --- ۶. ایجاد نوبت (Appointment) ---
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
            
            # --- ۷. هدایت (Redirect) نهایی ---
            
            if is_reception_booking:
                # اگر پذیرش در حال رزرو بود، سشن او را پاک کن
                if 'reception_acting_as_patient_id' in request.session:
                    del request.session['reception_acting_as_patient_id']
                
                if status == 'CONFIRMED': # تایید دستی
                    messages.success(request, f"نوبت برای {patient_user.username} با موفقیت (به صورت دستی) ثبت شد.")
                    # به سایر کارمندان اطلاع بده
                    staff_users = CustomUser.objects.filter(is_staff=True)
                    notification_link = request.build_absolute_uri(reverse('reception_panel:appointment_list'))
                    for staff in staff_users:
                        Notification.objects.create(
                            user=staff,
                            message=f"نوبت دستی جدید برای {patient_user.username} ثبت شد.",
                            link=notification_link
                        )
                
                else: # status == 'PENDING'
                    messages.success(request, f"نوبت برای {patient_user.username} ایجاد شد و در 'انتظار پرداخت' است.")
                    # به بیمار اطلاع بده که نوبتی در انتظار پرداخت دارد
                    notification_link = request.build_absolute_uri(reverse('users:dashboard'))
                    Notification.objects.create(
                        user=patient_user, # ارسال اعلان به بیمار
                        message=f"یک نوبت در انتظار پرداخت توسط پذیرش برای شما ثبت شد.",
                        link=notification_link
                    )

                # در هر صورت، پذیرش به داشبورد پنل خود بازمی‌گردد
                return redirect('reception_panel:dashboard')

            # اگر کاربر عادی بود، او را به صفحه پرداخت بفرست
            return redirect(reverse('payment:start_payment', args=[new_appointment.id]))

        except Exception as e:
            # مدیریت خطاهای پیش‌بینی نشده در طول تراکنش
            messages.error(request, f'خطایی در فرآیند رزرو رخ داد: {e}')
            return redirect('booking:create_booking')

    # --- منطق GET: نمایش فرم اولیه ---
    groups = ServiceGroup.objects.all()
    
    # --- *** اصلاحیه P2 (منطقه زمانی) *** ---
    # تاریخ "امروز" را بر اساس منطقه زمانی سرور (Asia/Tehran) بگیر
    # و به فرمت ISO (YYYY-MM-DD) به تمپلیت ارسال کن.
    today_server_gregorian = timezone.now().date()
    # --- *** پایان اصلاحیه P2 *** ---
    
    context = {
        'groups': groups,
        'user_points': initial_user_points,
        'max_discount': initial_max_discount,
        'patient_user_for_template': patient_user_for_template, # برای نمایش نام بیمار در فرم
        'today_date_server': today_server_gregorian.isoformat(), # <-- *** این خط باید وجود داشته باشد ***
    }
    return render(request, 'booking/create_booking.html', context)


@login_required
def rate_appointment_view(request, appointment_id):
    """
    ویو برای ثبت نظر (Testimonial) برای یک نوبت "انجام شده".
    """
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user,  # کاربر فقط می‌تواند نوبت خود را امتیاز دهد
        status='DONE',         # فقط نوبت‌های "انجام شده"
        is_rated=False         # فقط نوبت‌هایی که قبلاً امتیاز نداده
    )
    
    # نظر به اولین سرویس نوبت لینک می‌شود
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
                
                # --- اطلاع‌رسانی به کارمندان ---
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
                
                # نوبت را به "امتیازدهی شده" تغییر بده
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