# payment/views.py
"""
این فایل شامل ویوهای مربوط به فرآیند پرداخت است.
- start_payment_view: کاربر را برای پرداخت به درگاه هدایت می‌کند.
- payment_callback_view: پاسخ درگاه پس از پرداخت را مدیریت می‌کند.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from zarinpal import ZarinPal  # کتابخانه ارتباط با زرین‌پال
from .models import Transaction
from booking.models import Appointment
import json  # برای مدیریت خطاهای JSON
from django.urls import reverse
from reception_panel.models import Notification
from users.models import CustomUser


def start_payment_view(request, appointment_id):
    """
    ویو "شروع پرداخت".
    1. نوبت (Appointment) را پیدا می‌کند.
    2. مبلغ نهایی قابل پرداخت را محاسبه می‌کند.
    3. یک تراکنش (Transaction) در وضعیت "PENDING" ایجاد یا به‌روزرسانی می‌کند.
    4. به درگاه زرین‌پال متصل شده و "Authority" (کد رهگیری) دریافت می‌کند.
    5. کاربر را به صفحه پرداخت درگاه هدایت می‌کند.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    # محاسبه مبلغ نهایی بر اساس قیمت کل و "تمام" تخفیف‌های ثبت شده روی نوبت
    total_discount = appointment.points_discount_amount + appointment.code_discount_amount
    final_amount = appointment.get_total_price() - total_discount
    final_amount = max(0, final_amount)  # اطمینان از اینکه مبلغ منفی نیست

    # استفاده از update_or_create برای مدیریت تلاش‌های مجدد پرداخت:
    # اگر تراکنش "PENDING" از قبل وجود داشت، مبلغ و وضعیت آن را به‌روزرسانی
    # و authority قبلی را پاک می‌کند. اگر وجود نداشت، تراکنش جدید می‌سازد.
    transaction, created = Transaction.objects.update_or_create(
        appointment=appointment,
        defaults={
            'amount': final_amount,
            'status': 'PENDING',
            'authority': None  # پاک کردن رهگیری قبلی در هر تلاش مجدد
        }
    )

    # اتصال به زرین‌پال (در حالت Sandbox)
    client = ZarinPal(merchant_id=settings.ZARINPAL_MERCHANT_ID)
    client.sandbox = True
    
    request_data = {
        "amount": int(final_amount),
        "callback_url": settings.ZARINPAL_CALLBACK_URL,
        "description": f"پرداخت برای نوبت {appointment.get_services_display()}"
    }
    
    try:
        # ۱. درخواست به زرین‌پال برای دریافت Authority
        res = client.request(request_data)
        
        if res and res.data and res.data.code == 100 and res.data.authority:
            # ۲. ذخیره Authority در تراکنش
            transaction.authority = res.data.authority
            transaction.save()
            
            # ۳. ساخت URL پرداخت و هدایت کاربر
            payment_url = f'https://sandbox.zarinpal.com/pg/StartPay/{res.data.authority}'
            return redirect(payment_url)
        else:
            # اگر زرین‌پال Authority ندهد (مثلاً به دلیل خطای سرور)
            print(f"Failed to get authority from Zarinpal. Errors: {res.errors}")
            # --- مدیریت خطا: آزادسازی اسلات ---
            transaction.status = 'FAILED'
            transaction.save()
            if transaction.appointment.status == 'PENDING':
                transaction.appointment.status = 'CANCELED'
                transaction.appointment.save()
            # ------------------------------------
            return render(request, 'payment/payment_failed.html', {'error_message': 'خطا در ارتباط با درگاه پرداخت.'})

    except (json.JSONDecodeError, Exception) as e:
        # مدیریت خطاهای اتصال یا پاسخ نامعتبر از درگاه
        print(f"An unexpected error occurred during Zarinpal request: {e}")
        transaction.status = 'FAILED'
        transaction.save()
        # --- مدیریت خطا: آزادسازی اسلات ---
        if transaction.appointment.status == 'PENDING':
            transaction.appointment.status = 'CANCELED'
            transaction.appointment.save()
        # ------------------------------------
        return render(request, 'payment/payment_failed.html', {'error_message': 'خطا در پاسخ‌دهی درگاه پرداخت.'})


def payment_callback_view(request):
    """
    ویو "بازگشت از پرداخت" (Callback).
    این ویو توسط زرین‌پال پس از اتمام عملیات پرداخت (موفق یا ناموفق)
    فراخوانی می‌شود.
    """
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')  # 'OK' یا 'NOK'

    # تراکنش را بر اساس Authority بازگشتی پیدا کن
    transaction = get_object_or_404(Transaction, authority=authority)
    client = ZarinPal(merchant_id=settings.ZARINPAL_MERCHANT_ID)
    client.sandbox = True

    if status == 'OK':
        # --- پرداخت توسط کاربر "انجام شده"، اکنون باید "تایید" (Verify) شود ---
        verify_data = {
            "amount": int(transaction.amount), 
            "authority": authority
        }
        
        try:
            # ۱. ارسال درخواست Verify به زرین‌پال
            res = client.verify(verify_data)
            
            if res and res.data and res.data.code in [100, 101]:
                # --- پرداخت موفق و تایید شده (Code 100) ---
                # (Code 101 یعنی قبلا تایید شده، که باز هم موفق است)
                
                transaction.status = 'SUCCESS'
                transaction.appointment.status = 'CONFIRMED'
                transaction.save()
                transaction.appointment.save()
                
                # --- منطق پس از پرداخت موفق ---
                appointment = transaction.appointment
                
                # ۱. کسر امتیازات (اگر استفاده شده بود)
                if appointment.points_used > 0:
                    try:
                        profile = appointment.patient.profile
                        if profile.points >= appointment.points_used:
                            profile.points -= appointment.points_used
                            profile.save()
                        else:
                            print(f"Error: Not enough points for user {profile.user.username} (appointment {appointment.id})")
                    except Exception as e:
                        print(f"Error deducting points: {e}")

                # ۲. علامت‌گذاری کد تخفیف (اگر یکبار مصرف بود)
                if appointment.discount_code and appointment.discount_code.is_one_time:
                    try:
                        appointment.discount_code.is_used = True
                        appointment.discount_code.save()
                    except Exception as e:
                        print(f"Error marking discount code as used: {e}")
                
                # ۳. اطلاع‌رسانی به کارمندان
                staff_users = CustomUser.objects.filter(is_staff=True)
                notification_link = request.build_absolute_uri(reverse('reception_panel:appointment_list'))
                for staff in staff_users:
                    Notification.objects.create(
                        user=staff,
                        message=f"پرداخت نوبت {transaction.appointment.id} توسط {transaction.appointment.patient.username} با موفقیت انجام شد.",
                        link=notification_link
                    )

                return render(request, 'payment/payment_success.html', {'ref_id': res.data.ref_id})

        except (json.JSONDecodeError, Exception) as e:
            # خطای Verify: اگر در تایید پرداخت خطا رخ دهد (مثلاً سرور زرین‌پال قطع باشد)
            print(f"Error during payment verification: {e}")
            transaction.status = 'FAILED'
            transaction.save()
            # --- آزادسازی اسلات ---
            if transaction.appointment.status == 'PENDING':
                transaction.appointment.status = 'CANCELED'
                transaction.appointment.save()
            return render(request, 'payment/payment_failed.html')

    # --- پرداخت ناموفق (کاربر انصراف داده یا Status = 'NOK') ---
    
    transaction.status = 'FAILED'
    transaction.save()
    # --- آزادسازی اسلات ---
    if transaction.appointment.status == 'PENDING':
        transaction.appointment.status = 'CANCELED'
        transaction.appointment.save()
        
    return render(request, 'payment/payment_failed.html', {'error_message': 'پرداخت توسط شما لغو شد یا ناموفق بود.'})