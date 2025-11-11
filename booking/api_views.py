# booking/api_views.py
# فایل اصلاح‌شده: APIهای قدیمی تقوim حذف و با یک API واحد جایگزین شدند.

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

# --- وارد کردن توابع کمکی ---
# (اینها برای APIهای غیر-تقویمی استفاده می‌شوند)
from .utils import _get_patient_for_booking 
# --- وارد کردن «مغز متفکر» جدید تقوim ---
from .calendar_logic import generate_available_slots_for_range


# ***
# *** API جدید و واحد برای FullCalendar ***
# ***
def all_available_slots_api(request):
    """
    API واحد و جدید که تمام اسلات‌های خالی در یک بازه زمانی را
    برای FullCalendar برمی‌گرداند.
    """
    
    # --- ۱. دریافت پارامترهای ارسالی از کلاینت ---
    
    # FullCalendar این دو پارامتر را به صورت خودکار ارسال می‌کند
    start_str = request.GET.get('start', '').split('T')[0]
    end_str = request.GET.get('end', '').split('T')[0]

    # این پارامترها را ما به صورت دستی از فرم اضافه خواهیم کرد
    service_ids = request.GET.getlist('service_ids[]')
    device_id = request.GET.get('device_id')
    
    try:
        # اگر تاریخ‌ها ارسال نشده بودند، یک بازه پیش‌فرض (مثلاً ۶۰ روز) در نظر بگیر
        if not start_str or not end_str:
            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=60)
        else:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # اگر خدمات یا مدت زمان انتخاب نشده باشد، API نباید خطایی بدهد
    # بلکه فقط یک لیست خالی برگرداند تا تقوim خالی بماند.
    if not service_ids:
        return JsonResponse([], safe=False) # FullCalendar انتظار یک لیست را دارد

    # --- ۲. تعیین هویت بیمار ---
    # (کپی شده از API قدیمی - بدون تغییر)
    patient_user = request.user
    if request.user.is_staff and request.session.get('reception_acting_as_patient_id'):
        try:
            patient_user = CustomUser.objects.get(id=request.session['reception_acting_as_patient_id'])
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=400)

    # --- ۳. فراخوانی «مغز متفکر» ---
    available_slots = generate_available_slots_for_range(
        start_date=start_date,
        end_date=end_date,
        service_ids=service_ids,
        device_id=device_id,
        patient_user=patient_user
    )

    # --- ۴. برگرداندن پاسخ JSON ---
    # FullCalendar انتظار دارد هر اسلات خالی، یک "رویداد" (Event) باشد.
    # ما فرمت خروجی را کمی تغییر می‌دهیم تا FullCalendar آن را بفهمد.
    events = []
    for slot in available_slots:
        events.append({
            'id': f"{slot['start']}_{service_ids}", # یک شناسه موقت
            'start': slot['start'],
            'end': slot['end'],
            'title': 'رزرو', # عنوانی که روی اسلات در تقوim (اگر بخواهیم) نمایش داده می‌شود
            'display': 'background' # اسلات‌ها را به عنوان "پس‌زمینه در دسترس" نشان می‌دهد
        })

    return JsonResponse(events, safe=False)


# --------------------------------------------------------------------
# --- APIهای زیر دست‌نخورده باقی می‌مانند ---
# --------------------------------------------------------------------

def get_services_for_group_api(request):
    """ (بدون تغییر) - برای پر کردن لیست خدمات در فرم استفاده می‌شود """
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
        return JsonResponse({'error': 'Group not found'}, status=44)


@require_POST
@login_required
def apply_discount_api(request):
    """ (بدون تغییر) - برای اعمال کد تخفیف استفاده می‌شود """
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
