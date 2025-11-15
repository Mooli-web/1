# booking/api_views.py
# فایل اصلاح‌شده: API تقوim دیگر به پارامترهای start/end وابسته نیست.

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, time, timedelta # <-- timedelta وارد شده است
# import jdatetime # <-- دیگر نیازی نیست

from clinic.models import Service, DiscountCode, ServiceGroup, Device, WorkHours
from .models import Appointment
from users.models import CustomUser

from .utils import _get_patient_for_booking 
from .calendar_logic import generate_available_slots_for_range


# ***
# *** API جدید و واحد (اصلاح شده) ***
# ***
def all_available_slots_api(request):
    """
    API واحد که تمام اسلات‌های خالی در 30 روز آینده را
    برمی‌گرداند.
    """
    
    # --- ۱. دریافت پارامترهای ارسالی از کلاینت ---
    
    # --- این بخش حذف شد ---
    # start_str = request.GET.get('start', '')...
    # end_str = request.GET.get('end', '')...

    # +++ این بخش اضافه شد +++
    # همیشه یک بازه 30 روزه از امروز محاسبه کن
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=30)
    # +++ پایان بخش اضافه شده +++


    service_ids = request.GET.getlist('service_ids[]')
    device_id = request.GET.get('device_id')
    
    if not service_ids:
        return JsonResponse([], safe=False)

    # --- ۲. تعیین هویت بیمار (بدون تغییر) ---
    patient_user = request.user
    if request.user.is_staff and request.session.get('reception_acting_as_patient_id'):
        try:
            patient_user = CustomUser.objects.get(id=request.session['reception_acting_as_patient_id'])
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=400)

    # --- ۳. فراخوانی «مغز متفکر» (بدون تغییر) ---
    available_slots = generate_available_slots_for_range(
        start_date=start_date,
        end_date=end_date,
        service_ids=service_ids,
        device_id=device_id,
        patient_user=patient_user
    )

    # --- ۴. برگرداندن پاسخ JSON (بدون تغییر) ---
    # ما دیگر به فرمت event برای FullCalendar نیازی نداریم،
    # اما همین فرمت لیست ساده از دیکشنری‌ها برای JS ما عالی است.
    return JsonResponse(available_slots, safe=False)


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