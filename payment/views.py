# a_copy/payment/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from zarinpal import ZarinPal
from .models import Transaction
from booking.models import Appointment
# --- REMOVED: Celery task import ---
# from booking.tasks import send_appointment_reminder_email
from datetime import timedelta
# این import را برای مدیریت خطای JSON اضافه کنید
import json
# --- TASK 1: Import Notification requirements ---
from django.urls import reverse
from reception_panel.models import Notification
from users.models import CustomUser


def start_payment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

    # --- CORRECTED: Calculate final amount based on all discounts AND total price ---
    total_discount = appointment.points_discount_amount + appointment.code_discount_amount
    final_amount = appointment.get_total_price() - total_discount # <-- CHANGED
    # Ensure amount is not negative
    final_amount = max(0, final_amount)

    # --- BUG FIX (Task 4): Use update_or_create to re-validate price ---
    transaction, created = Transaction.objects.update_or_create(
        appointment=appointment,
        defaults={
            'amount': final_amount,
            'status': 'PENDING',
            'authority': None # پاک کردن رهگیری قبلی در هر تلاش مجدد
        }
    )

    client = ZarinPal(merchant_id=settings.ZARINPAL_MERCHANT_ID)
    client.sandbox = True
    
    request_data = {
        "amount": int(final_amount),
        "callback_url": settings.ZARINPAL_CALLBACK_URL,
        "description": f"پرداخت برای نوبت {appointment.get_services_display()}" # <-- CHANGED
    }
    
    try:
        # درخواست به زرین‌پال را در یک بلوک try قرار می‌دهیم
        res = client.request(request_data)
        
        if res and res.data and res.data.code == 100 and res.data.authority:
            transaction.authority = res.data.authority
            transaction.save()
            
            payment_url = f'https://sandbox.zarinpal.com/pg/StartPay/{res.data.authority}'
            
            print(f"Redirecting to Zarinpal URL: {payment_url}") 
            
            return redirect(payment_url)
        else:
            print(f"Failed to get authority from Zarinpal. Errors: {res.errors}")
            
            # --- BUG 1 FIX: Set status to FAILED and CANCELED ---
            transaction.status = 'FAILED'
            transaction.save()
            if transaction.appointment.status == 'PENDING':
                transaction.appointment.status = 'CANCELED'
                transaction.appointment.save()
            # --------------------------------------------------
            
            return render(request, 'payment/payment_failed.html', {'error_message': 'خطا در ارتباط با درگاه پرداخت.'})

    except json.JSONDecodeError:
        # اگر پاسخ زرین‌پال JSON معتبر نباشد، این خطا رخ می‌دهد
        print("JSONDecodeError: Failed to parse response from Zarinpal.")
        transaction.status = 'FAILED'
        transaction.save()
        # --- ADDED: Task 4 - Instant Slot Release ---
        if transaction.appointment.status == 'PENDING':
            transaction.appointment.status = 'CANCELED'
            transaction.appointment.save()
        return render(request, 'payment/payment_failed.html', {'error_message': 'پاسخ نامعتبر از درگاه پرداخت. لطفاً لحظاتی دیگر دوباره تلاش کنید.'})
    except Exception as e:
        # مدیریت خطاهای دیگر (مانند خطای اتصال)
        print(f"An unexpected error occurred: {e}")
        transaction.status = 'FAILED'
        transaction.save()
        # --- ADDED: Task 4 - Instant Slot Release ---
        if transaction.appointment.status == 'PENDING':
            transaction.appointment.status = 'CANCELED'
            transaction.appointment.save()
        return render(request, 'payment/payment_failed.html', {'error_message': 'یک خطای پیش‌بینی‌نشده رخ داد.'})


def payment_callback_view(request):
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')

    transaction = get_object_or_404(Transaction, authority=authority)
    client = ZarinPal(merchant_id=settings.ZARINPAL_MERCHANT_ID)
    client.sandbox = True

    if status == 'OK':
        verify_data = {
            "amount": int(transaction.amount), 
            "authority": authority
        }
        
        try:
            res = client.verify(verify_data)
            
            if res and res.data and res.data.code in [100, 101]:
                transaction.status = 'SUCCESS'
                transaction.appointment.status = 'CONFIRMED'
                transaction.save()
                transaction.appointment.save()
                
                # --- REMOVED: Celery task call for reminder ---
                
                # --- BUG FIX (Task 5): Apply points/code *after* successful payment ---
                appointment = transaction.appointment
                
                # 1. Deduct points
                if appointment.points_used > 0:
                    try:
                        profile = appointment.patient.profile
                        if profile.points >= appointment.points_used:
                            profile.points -= appointment.points_used
                            profile.save()
                        else:
                            # اگر امتیاز کافی نبود (اتفاق نادر)، خطا را لاگ کن
                            print(f"Error: Not enough points for user {profile.user.username} (appointment {appointment.id})")
                    except Exception as e:
                        print(f"Error deducting points: {e}")

                # 2. Mark discount code as used
                if appointment.discount_code:
                    try:
                        if appointment.discount_code.is_one_time:
                            appointment.discount_code.is_used = True
                            appointment.discount_code.save()
                    except Exception as e:
                        print(f"Error marking discount code as used: {e}")
                # --- END BUG FIX ---
                
                # --- TASK 1: Notify staff of successful payment ---
                staff_users = CustomUser.objects.filter(is_staff=True)
                notification_link = request.build_absolute_uri(
                    reverse('reception_panel:appointment_list')
                )
                for staff in staff_users:
                    Notification.objects.create(
                        user=staff,
                        message=f"پرداخت نوبت {transaction.appointment.id} توسط {transaction.appointment.patient.username} با موفقیت انجام شد.",
                        link=notification_link
                    )

                return render(request, 'payment/payment_success.html', {'ref_id': res.data.ref_id})

        except (json.JSONDecodeError, Exception) as e:
            print(f"Error during payment verification: {e}")
            # --- ADDED: Task 4 - Instant Slot Release on verification failure ---
            if transaction.appointment.status == 'PENDING':
                transaction.appointment.status = 'CANCELED'
                transaction.appointment.save()
            # اگر در مرحله تایید هم خطا رخ داد، تراکنش را ناموفق ثبت کن
            transaction.status = 'FAILED'
            transaction.save()
            return render(request, 'payment/payment_failed.html')

    # --- ADDED: Task 4 - Instant Slot Release on non-OK status ---
    if transaction.appointment.status == 'PENDING':
        transaction.appointment.status = 'CANCELED'
        transaction.appointment.save()
        
    transaction.status = 'FAILED'
    transaction.save()
    return render(request, 'payment/payment_failed.html', {'error_message': 'پاسخ نامعتبر از درگاه پرداخت. لطفاً لحظاتی دیگر دوباره تلاش کنید.'})