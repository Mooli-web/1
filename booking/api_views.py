# booking/api_views.py
"""
این فایل شامل تمام Endpoints (نقاط پایانی) API است که
توسط جاوا اسکریپت فرانت‌اند (booking.js) برای ایجاد یک
فرم رزرو پویا فراخوانی می‌شوند.
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta

from clinic.models import Service, DiscountCode, ServiceGroup, Device
from users.models import CustomUser

# توابع کمکی
from .utils import _get_patient_for_booking 
# "مغز متفکر" تقویم
from .calendar_logic import generate_available_slots_for_range


def all_available_slots_api(request):
    """
    API اصلی برای دریافت اسلات‌های خالی.
    این API از JS فراخوانی می‌شود و یک بازه 30 روزه از "امروز" را محاسبه
    و در قالب JSON برمی‌گرداند.
    """
    
    # --- ۱. محاسبه بازه زمانی ---
    # این API همیشه یک بازه 30 روزه از امروز را محاسبه می‌کند
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=30)

    # --- ۲. دریافت پارامترها از کلاینت (Query Params) ---
    service_ids = request.GET.getlist('service_ids[]')
    device_id = request.GET.get('device_id')
    
    if not service_ids:
        # اگر هیچ خدمتی انتخاب نشده، لیست خالی برگردان
        return JsonResponse([], safe=False)

    # --- ۳. تعیین هویت بیمار ---
    # (تشخیص اینکه آیا پذیرش در حال رزرو است یا خود بیمار)
    patient_user, _, _ = _get_patient_for_booking(request)
    if patient_user is None or not patient_user.is_authenticated:
        # (توجه: اگر بیمار لاگین نباشد، فیلتر جنسیت کار نمی‌کند
        # اما _get_patient_for_booking کاربر request.user را برمی‌گرداند
        # که اگر لاگین نباشد، AnonymousUser است و patient_user.gender
        # به سادگی None می‌شود و فیلتر جنسیت فقط 'ALL' را برمی‌گرداند)
        
        # اگر بخواهیم رزرو فقط برای کاربران لاگین شده باشد، باید اینجا
        # return JsonResponse({'error': 'Authentication required'}, status=401)
        # قرار دهیم. اما بر اساس کد موجود، به نظر می‌رسد رزرو
        # برای کاربر Anonymous (که بعداً لاگین می‌کند) مجاز است.
        # *اصلاح*: ویو create_booking نیاز به @login_required دارد،
        # پس patient_user همیشه Anonymous نیست، مگر اینکه دکوریتور
        # از روی all_available_slots_api حذف شده باشد (که شده).
        # با این حال، _get_patient_for_booking این را مدیریت می‌کند.
        pass # اجازه می‌دهیم ادامه یابد

    if not patient_user.is_authenticated:
         return JsonResponse({'error': 'Patient not found or not authenticated'}, status=400)


    # --- ۴. فراخوانی "مغز متفکر" ---
    available_slots = generate_available_slots_for_range(
        start_date=start_date,
        end_date=end_date,
        service_ids=service_ids,
        device_id=device_id,
        patient_user=patient_user
    )

    # --- ۵. برگرداندن پاسخ JSON ---
    # خروجی یک لیست ساده از دیکشنری‌ها است که JS آن را مدیریت می‌کند
    return JsonResponse(available_slots, safe=False)


# --------------------------------------------------------------------
# --- APIهای کمکی فرم ---
# --------------------------------------------------------------------

def get_services_for_group_api(request):
    """
    API کمکی (AJAX).
    وقتی کاربر "گروه خدمت" را انتخاب می‌کند، این API فراخوانی می‌شود
    تا لیست "خدمات" (زیرگروه‌ها) و "دستگاه‌ها"ی آن گروه را
    دریافت کند و فرم را به صورت پویا پر کند.
    """
    group_id = request.GET.get('group_id')
    if not group_id:
        return JsonResponse({'error': 'Missing group_id'}, status=400)
    try:
        # prefetch_related برای بهینه‌سازی دسترسی به دستگاه‌ها (M2M)
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


@require_POST
@login_required  # کاربر برای اعمال تخفیف باید لاگین باشد
def apply_discount_api(request):
    """
    API کمکی (AJAX).
    برای اعتبارسنجی "کد تخفیف" و محاسبه مبلغ تخفیف قبل از
    ثبت نهایی فرم استفاده می‌شود.
    """
    code = request.POST.get('code', '').strip()
    total_price_str = request.POST.get('total_price', '0')
    
    # تعیین هویت بیمار (پذیرش یا خود بیمار)
    patient_user, _, _ = _get_patient_for_booking(request)
    if patient_user is None or not patient_user.is_authenticated:
         return JsonResponse({'status': 'error', 'message': 'بیمار یافت نشد.'}, status=404)

    try:
        total_price = float(total_price_str)
    except ValueError:
        total_price = 0

    if not code or total_price == 0:
        return JsonResponse({'status': 'error', 'message': 'کد یا مبلغ نامعتبر است.'}, status=400)

    # --- اعتبارسنجی کد تخفیف ---
    try:
        discount_code = DiscountCode.objects.get(code__iexact=code)

        if not discount_code.is_valid():
            return JsonResponse({'status': 'error', 'message': 'کد تخفیف معتبر نیست یا منقضی شده.'}, status=400)
            
        if discount_code.user and discount_code.user != patient_user:
            return JsonResponse({'status': 'error', 'message': 'این کد تخفیف مخصوص شما نیست.'}, status=400)
            
        if discount_code.is_one_time and discount_code.is_used:
             return JsonResponse({'status': 'error', 'message': 'این کد تخفیف قبلاً استفاده شده است.'}, status=400)

        # محاسبه مبلغ تخفیف
        discount_amount = 0
        if discount_code.discount_type == 'PERCENTAGE':
            discount_amount = (total_price * discount_code.value) / 100
        else: # FIXED_AMOUNT
            discount_amount = discount_code.value

        return JsonResponse({'status': 'success', 'discount_amount': discount_amount})

    except DiscountCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'کد تخفیFف یافت نشد.'}, status=404)