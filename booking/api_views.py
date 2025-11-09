# booking/api_views.py
# فایل جدید: این فایل شامل ویوهای API است که پاسخ JSON برمی‌گردانند.

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, time, timedelta
import jdatetime

from clinic.models import Service, DiscountCode, ServiceGroup, Device, WorkHours
from .models import Appointment
from users.models import CustomUser

# توابع کمکی را از utils.py وارد می‌کنیم
from .utils import get_available_slots_for_day


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