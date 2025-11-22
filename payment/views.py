# payment/views.py
"""
ویوهای مدیریت پرداخت (اتصال به درگاه زرین‌پال).
شامل: شروع پرداخت و مدیریت بازگشت (Callback).
"""

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.urls import reverse
from django.db import transaction as db_transaction # تغییر نام برای جلوگیری از تداخل با مدل Transaction
from django.http import HttpRequest, HttpResponse

from zarinpal import ZarinPal
from .models import Transaction
from booking.models import Appointment
from reception_panel.models import Notification
from users.models import CustomUser

def start_payment_view(request: HttpRequest, appointment_id: int) -> HttpResponse:
    """
    شروع فرآیند پرداخت.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    # 1. محاسبه مبلغ نهایی
    total_discount = appointment.points_discount_amount + appointment.code_discount_amount
    # استفاده از get_total_price() که ممکن است کوئری بزند، در اینجا برای یک آیتم مشکلی نیست
    final_amount = appointment.get_total_price() - total_discount
    final_amount = max(0, int(final_amount))

    if final_amount == 0:
        # اگر مبلغ صفر است (مثلا با تخفیف)، شاید باید مستقیماً تایید شود؟
        # فعلاً فرض بر این است که همیشه مبلغی برای پرداخت وجود دارد یا درگاه اجازه 0 نمی‌دهد.
        pass

    # 2. ایجاد یا بروزرسانی تراکنش
    txn_obj, created = Transaction.objects.update_or_create(
        appointment=appointment,
        defaults={
            'amount': final_amount,
            'status': 'PENDING',
            'authority': None 
        }
    )

    # 3. اتصال به درگاه
    # تنظیم سندباکس بر اساس Debug بودن پروژه
    client = ZarinPal(merchant_id=settings.ZARINPAL_MERCHANT_ID)
    client.sandbox = settings.DEBUG 
    
    req_data = {
        "amount": final_amount,
        "callback_url": settings.ZARINPAL_CALLBACK_URL,
        "description": f"پرداخت نوبت {appointment.id} - {request.user.username}"
    }
    
    try:
        res = client.request(req_data)
        
        if res and res.data and res.data.code == 100 and res.data.authority:
            txn_obj.authority = res.data.authority
            txn_obj.save(update_fields=['authority'])
            
            return redirect(f'https://sandbox.zarinpal.com/pg/StartPay/{res.data.authority}' if settings.DEBUG else f'https://www.zarinpal.com/pg/StartPay/{res.data.authority}')
        else:
            # خطای منطقی درگاه (مثلاً مبلغ نامعتبر)
            _handle_failed_payment(txn_obj)
            return render(request, 'payment/payment_failed.html', {'error_message': 'خطا در دریافت پاسخ از درگاه.'})

    except Exception as e:
        print(f"ZarinPal Request Error: {e}")
        _handle_failed_payment(txn_obj)
        return render(request, 'payment/payment_failed.html', {'error_message': 'خطای سیستمی در اتصال به درگاه.'})


def payment_callback_view(request: HttpRequest) -> HttpResponse:
    """
    بازگشت از درگاه پرداخت.
    مدیریت Idempotency (جلوگیری از پردازش تکراری) و تراکنش‌های اتمیک.
    """
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')

    txn_obj = get_object_or_404(Transaction.objects.select_related('appointment__patient__profile', 'appointment__discount_code'), authority=authority)
    
    # --- Idempotency Check ---
    # اگر تراکنش قبلاً موفق شده، نیازی به پردازش مجدد نیست
    if txn_obj.status == 'SUCCESS':
        return render(request, 'payment/payment_success.html', {'ref_id': 'Already Verified'})

    # اگر درگاه وضعیت NOK برگرداند
    if status != 'OK':
        _handle_failed_payment(txn_obj)
        return render(request, 'payment/payment_failed.html', {'error_message': 'پرداخت توسط کاربر لغو شد یا ناموفق بود.'})

    # --- تایید پرداخت (Verification) ---
    client = ZarinPal(merchant_id=settings.ZARINPAL_MERCHANT_ID)
    client.sandbox = settings.DEBUG

    verify_data = {
        "amount": int(txn_obj.amount), 
        "authority": authority
    }

    try:
        res = client.verify(verify_data)
        
        # کدهای موفقیت زرین‌پال: 100 (موفق)، 101 (قبلاً وریفای شده)
        if res and res.data and res.data.code in [100, 101]:
            
            # --- شروع تراکنش اتمیک دیتابیس ---
            # این بلوک تضمین می‌کند که یا همه تغییرات اعمال می‌شوند یا هیچ‌کدام.
            with db_transaction.atomic():
                
                # 1. آپدیت تراکنش
                txn_obj.status = 'SUCCESS'
                txn_obj.save(update_fields=['status'])
                
                # 2. آپدیت نوبت
                appointment = txn_obj.appointment
                appointment.status = 'CONFIRMED'
                appointment.save(update_fields=['status'])
                
                # 3. کسر امتیاز (اگر استفاده شده)
                if appointment.points_used > 0:
                    profile = appointment.patient.profile
                    if profile.points >= appointment.points_used:
                        profile.points -= appointment.points_used
                        profile.save(update_fields=['points'])
                
                # 4. باطل کردن کد تخفیف (اگر یکبار مصرف است)
                if appointment.discount_code and appointment.discount_code.is_one_time:
                    appointment.discount_code.is_used = True
                    appointment.discount_code.save(update_fields=['is_used'])
                
                # 5. نوتیفیکیشن (اگر خطا داد، کل تراکنش رول‌بک می‌شود که امن‌تر است)
                _send_success_notifications(request, appointment, txn_obj)

            return render(request, 'payment/payment_success.html', {'ref_id': res.data.ref_id})
        
        else:
            # خطای وریفای (مثلاً عدم تطابق مبلغ)
            _handle_failed_payment(txn_obj)
            return render(request, 'payment/payment_failed.html')

    except Exception as e:
        print(f"ZarinPal Verify Error: {e}")
        # در صورت خطای کدنویسی یا شبکه در مرحله وریفای، بهتر است وضعیت را فیل نکنیم تا کاربر بتواند پیگیری کند
        # اما فعلاً طبق روال سیستم FAILED می‌کنیم
        _handle_failed_payment(txn_obj)
        return render(request, 'payment/payment_failed.html')


def _handle_failed_payment(transaction):
    """تابع کمکی برای مدیریت شکست پرداخت"""
    transaction.status = 'FAILED'
    transaction.save(update_fields=['status'])
    
    # آزاد کردن نوبت برای رزرو مجدد
    if transaction.appointment.status == 'PENDING':
        transaction.appointment.status = 'CANCELED'
        transaction.appointment.save(update_fields=['status'])

def _send_success_notifications(request, appointment, transaction):
    """تابع کمکی ارسال اعلان"""
    staff_users = CustomUser.objects.filter(is_staff=True)
    if staff_users.exists():
        link = request.build_absolute_uri(reverse('reception_panel:appointment_list'))
        notifications = [
            Notification(
                user=staff,
                message=f"پرداخت نوبت {appointment.id} ({appointment.patient.username}) موفق بود.",
                link=link
            ) for staff in staff_users
        ]
        Notification.objects.bulk_create(notifications)