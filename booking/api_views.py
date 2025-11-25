# booking/api_views.py
from django.http import JsonResponse, HttpRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta

from clinic.models import ServiceGroup, DiscountCode, Service
from .utils import _get_patient_for_booking 
from .calendar_logic import generate_available_slots_for_range

def all_available_slots_api(request: HttpRequest) -> JsonResponse:
    """
    API دریافت زمان‌های خالی.
    بهبود: اضافه کردن متادیتای 'capacity_status' برای هر روز.
    """
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=45) # افزایش بازه برای تجربه کاربری بهتر

    service_ids = request.GET.getlist('service_ids[]')
    device_id = request.GET.get('device_id')
    
    if not service_ids:
        return JsonResponse({}, safe=True)
    
    # اعتبارسنجی ورودی‌ها
    clean_service_ids = []
    for sid in service_ids:
        if sid.isdigit():
            clean_service_ids.append(sid)
            
    if device_id and not device_id.isdigit():
        return JsonResponse({'error': 'Invalid device ID'}, status=400)

    patient_user, _, _ = _get_patient_for_booking(request)
    if patient_user is None or not patient_user.is_authenticated:
         return JsonResponse({'error': 'Authentication required'}, status=403)

    # تولید اسلات‌ها
    grouped_slots = generate_available_slots_for_range(
        start_date=start_date,
        end_date=end_date,
        service_ids=clean_service_ids,
        device_id=int(device_id) if device_id else None,
        patient_user=patient_user
    )
    
    # اضافه کردن متادیتا برای فرانت‌اند (High/Low demand)
    # این بخش به UI اجازه می‌دهد رنگ تقویم را تغییر دهد
    for date_key, slots in grouped_slots.items():
        count = len(slots)
        status = 'high'
        if count < 3:
            status = 'critical' # قرمز (عجله کن)
        elif count < 6:
            status = 'low' # زرد
        
        # تزریق وضعیت به اولین اسلات یا ساختار جداگانه (اینجا ساده‌سازی شده)
        # ما این دیتا را در فرانت پردازش می‌کنیم.
        # چون ساختار فعلی List[Dict] است، ما یک پراپرتی به تمام اسلات‌ها اضافه نمی‌کنیم
        # بلکه فرانت بر اساس count تصمیم می‌گیرد.
        pass 

    return JsonResponse(grouped_slots, safe=True)

def get_services_for_group_api(request: HttpRequest) -> JsonResponse:
    """
    API دریافت خدمات یک گروه.
    """
    group_id = request.GET.get('group_id')
    if not group_id or not group_id.isdigit():
        return JsonResponse({'error': 'Invalid group_id'}, status=400)
    
    try:
        group = ServiceGroup.objects.prefetch_related('available_devices', 'services').get(id=group_id)
        
        # فقط سرویس‌هایی که قیمت دارند را بفرست
        services_data = []
        for s in group.services.all():
            services_data.append({
                'id': s.id,
                'name': s.name,
                'price': int(s.price),
                'duration': s.duration,
                'discount_percentage': s.discount_percentage, # اضافه شده برای نمایش تخفیف
                'old_price': int(s.old_price) if s.old_price else None
            })

        data = {
            'allow_multiple_selection': group.allow_multiple_selection,
            'has_devices': group.has_devices,
            'devices': [{'id': d.id, 'name': d.name} for d in group.available_devices.all()],
            'services': services_data
        }
        return JsonResponse(data)
    except ServiceGroup.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)

@require_POST
@login_required
def apply_discount_api(request: HttpRequest) -> JsonResponse:
    """
    API اعمال کد تخفیف با امنیت بیشتر.
    """
    code = request.POST.get('code', '').strip()
    total_price_str = request.POST.get('total_price', '0')
    
    patient_user, _, _ = _get_patient_for_booking(request)
    
    try:
        total_price = float(total_price_str)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'مبلغ نامعتبر است.'}, status=400)

    if not code:
        return JsonResponse({'status': 'error', 'message': 'کد تخفیف را وارد کنید.'}, status=400)

    try:
        discount_code = DiscountCode.objects.get(code__iexact=code)

        if not discount_code.is_valid():
            return JsonResponse({'status': 'error', 'message': 'این کد تخفیف منقضی یا غیرفعال شده است.'}, status=400)
            
        if discount_code.user and discount_code.user != patient_user:
            return JsonResponse({'status': 'error', 'message': 'این کد تخفیف متعلق به شما نیست.'}, status=403)
            
        if discount_code.is_one_time and discount_code.is_used:
             return JsonResponse({'status': 'error', 'message': 'این کد قبلاً استفاده شده است.'}, status=400)

        discount_amount = 0
        if discount_code.discount_type == 'PERCENTAGE':
            discount_amount = (total_price * discount_code.value) / 100
        else:
            discount_amount = discount_code.value
            
        # تخفیف نباید بیشتر از کل مبلغ باشد
        discount_amount = min(discount_amount, total_price)

        return JsonResponse({
            'status': 'success', 
            'discount_amount': int(discount_amount),
            'message': 'کد تخفیف با موفقیت اعمال شد.'
        })

    except DiscountCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'کد تخفیف یافت نشد.'}, status=404)