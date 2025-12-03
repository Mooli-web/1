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
    تغییرات:
    1. حذف شرط لاگین اجباری.
    2. دریافت پارامترهای services و device.
    """
    # بازه زمانی (مثلاً تا ۴۵ روز آینده)
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=45)

    service_ids = request.GET.getlist('service_ids[]')
    device_id = request.GET.get('device_id')
    
    # اگر سرویسی انتخاب نشده، تقویم خالی برگردان
    if not service_ids:
        return JsonResponse({}, safe=True)
    
    # تمیزکاری ورودی‌ها
    clean_service_ids = []
    for sid in service_ids:
        if sid.isdigit():
            clean_service_ids.append(sid)
            
    if device_id and not device_id.isdigit():
        return JsonResponse({'error': 'Invalid device ID'}, status=400)

    # دریافت کاربر (ممکن است None باشد)
    patient_user, _, _ = _get_patient_for_booking(request)
    
    # نکته مهم: اینجا قبلاً شرط چک کردن لاگین بود که حذف شد.
    
    # تولید اسلات‌ها
    # حتما مطمئن شوید فایل calendar_logic.py هم آپدیت شده باشد
    grouped_slots = generate_available_slots_for_range(
        start_date=start_date,
        end_date=end_date,
        service_ids=clean_service_ids,
        device_id=int(device_id) if device_id else None,
        patient_user=patient_user,
        # اگر می‌خواهید برای مهمان پیش‌فرض خاصی بفرستید، اینجا اضافه کنید
        # اما لاجیک داخل calendar_logic.py که قبلا فرستادم خودش هندل می‌کند.
    )
    
    return JsonResponse(grouped_slots, safe=True)

def get_services_for_group_api(request: HttpRequest) -> JsonResponse:
    """
    API دریافت خدمات یک گروه برای نمایش در کارت‌ها.
    """
    group_id = request.GET.get('group_id')
    if not group_id or not group_id.isdigit():
        return JsonResponse({'error': 'Invalid group_id'}, status=400)
    
    try:
        group = ServiceGroup.objects.prefetch_related('available_devices', 'services').get(id=group_id)
        
        services_data = []
        for s in group.services.all():
            services_data.append({
                'id': s.id,
                'name': s.name,
                'price': int(s.price),
                'duration': s.duration,
                # این فیلدها برای نمایش در UI جدید لازم است
                'discount_percentage': s.discount_percentage, 
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
# @login_required  <-- این خط را حذف کردیم تا مهمان هم بتواند کد بزند
def apply_discount_api(request: HttpRequest) -> JsonResponse:
    """
    API اعمال کد تخفیف.
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
            
        # اگر کد اختصاصی کاربر خاصی است، چک کن کاربر لاگین شده همان باشد
        if discount_code.user:
            if not patient_user:
                return JsonResponse({'status': 'error', 'message': 'برای استفاده از این کد باید وارد شوید.'}, status=403)
            if discount_code.user != patient_user:
                return JsonResponse({'status': 'error', 'message': 'این کد تخفیف متعلق به شما نیست.'}, status=403)
            
        if discount_code.is_one_time and discount_code.is_used:
             return JsonResponse({'status': 'error', 'message': 'این کد قبلاً استفاده شده است.'}, status=400)

        discount_amount = 0
        if discount_code.discount_type == 'PERCENTAGE':
            discount_amount = (total_price * discount_code.value) / 100
        else:
            discount_amount = discount_code.value
            
        discount_amount = min(discount_amount, total_price)

        return JsonResponse({
            'status': 'success', 
            'discount_amount': int(discount_amount),
            'message': 'کد تخفیف با موفقیت اعمال شد.'
        })

    except DiscountCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'کد تخفیف یافت نشد.'}, status=404)