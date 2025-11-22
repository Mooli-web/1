# booking/api_views.py
"""
API endpoints برای سیستم رزرو نوبت.
این فایل توسط کلاینت (JS) برای دریافت اسلات‌های خالی و اعمال تخفیف فراخوانی می‌شود.
"""

from django.http import JsonResponse, HttpRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta

from clinic.models import ServiceGroup, DiscountCode
from .utils import _get_patient_for_booking 
from .calendar_logic import generate_available_slots_for_range

def all_available_slots_api(request: HttpRequest) -> JsonResponse:
    """
    API دریافت زمان‌های خالی (Slots).
    خروجی: JSON گروه‌بندی شده بر اساس تاریخ شمسی.
    """
    # 1. تنظیم بازه زمانی (30 روز آینده)
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=30)

    # 2. دریافت ورودی‌ها
    service_ids = request.GET.getlist('service_ids[]')
    device_id = request.GET.get('device_id')
    
    if not service_ids:
        return JsonResponse({}, safe=True)
    
    # تبدیل device_id به عدد صحیح در صورت وجود
    if device_id:
        try:
            device_id = int(device_id)
        except ValueError:
            return JsonResponse({'error': 'Invalid device ID'}, status=400)

    # 3. احراز هویت بیمار
    patient_user, _, _ = _get_patient_for_booking(request)
    if patient_user is None or not patient_user.is_authenticated:
         return JsonResponse({'error': 'Patient not found or not authenticated'}, status=403)

    # 4. محاسبه اسلات‌ها (Logic Core)
    grouped_slots = generate_available_slots_for_range(
        start_date=start_date,
        end_date=end_date,
        service_ids=service_ids,
        device_id=device_id,
        patient_user=patient_user
    )

    return JsonResponse(grouped_slots, safe=True)

def get_services_for_group_api(request: HttpRequest) -> JsonResponse:
    """
    API دریافت لیست خدمات یک گروه خاص.
    """
    group_id = request.GET.get('group_id')
    if not group_id:
        return JsonResponse({'error': 'Missing group_id'}, status=400)
    
    try:
        group = ServiceGroup.objects.prefetch_related('available_devices', 'services').get(id=group_id)
        
        data = {
            'allow_multiple_selection': group.allow_multiple_selection,
            'has_devices': group.has_devices,
            'devices': [
                {'id': d.id, 'name': d.name} for d in group.available_devices.all()
            ],
            'services': [
                {
                    'id': s.id,
                    'name': s.name,
                    'price': int(s.price), # اطمینان از ارسال عدد صحیح
                    'duration': s.duration,
                }
                for s in group.services.all()
            ]
        }
        return JsonResponse(data)
    except ServiceGroup.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)

@require_POST
@login_required
def apply_discount_api(request: HttpRequest) -> JsonResponse:
    """
    API اعمال کد تخفیف.
    """
    code = request.POST.get('code', '').strip()
    total_price_str = request.POST.get('total_price', '0')
    
    patient_user, _, _ = _get_patient_for_booking(request)
    if not patient_user:
         return JsonResponse({'status': 'error', 'message': 'کاربر نامعتبر است.'}, status=403)

    try:
        total_price = float(total_price_str)
    except ValueError:
        total_price = 0

    if not code or total_price <= 0:
        return JsonResponse({'status': 'error', 'message': 'اطلاعات ورودی نامعتبر است.'}, status=400)

    try:
        discount_code = DiscountCode.objects.get(code__iexact=code)

        if not discount_code.is_valid():
            return JsonResponse({'status': 'error', 'message': 'کد تخفیف معتبر نیست یا منقضی شده.'}, status=400)
            
        if discount_code.user and discount_code.user != patient_user:
            return JsonResponse({'status': 'error', 'message': 'این کد تخفیف متعلق به شما نیست.'}, status=403)
            
        if discount_code.is_one_time and discount_code.is_used:
             return JsonResponse({'status': 'error', 'message': 'این کد قبلاً استفاده شده است.'}, status=400)

        # محاسبه مقدار تخفیف
        if discount_code.discount_type == 'PERCENTAGE':
            discount_amount = (total_price * discount_code.value) / 100
        else: # FIXED_AMOUNT
            discount_amount = discount_code.value
            
        # تخفیف نباید از قیمت کل بیشتر باشد
        discount_amount = min(discount_amount, total_price)

        return JsonResponse({'status': 'success', 'discount_amount': int(discount_amount)})

    except DiscountCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'کد تخفیف یافت نشد.'}, status=404)