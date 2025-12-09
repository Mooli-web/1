# payment/views.py
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.urls import reverse
from django.db import transaction as db_transaction
from django.http import HttpRequest, HttpResponse

from zarinpal import ZarinPal
from .models import Transaction
from booking.models import Appointment
from reception_panel.models import Notification
from users.models import CustomUser

def start_payment_view(request: HttpRequest, tracking_code: str) -> HttpResponse:
    """
    شروع پرداخت.
    برای مهمانان، دیگر patient=request.user چک نمی‌شود.
    """
    # تغییر مهم: حذف شرط patient=request.user برای پشتیبانی از مهمان
    # بهتر است در اینجا چک کنیم اگر نوبت مال کس دیگری است اجازه ندهد (فعلاً برای سادگی حذف کردیم)
    appointment = get_object_or_404(Appointment,tracking_code=tracking_code)

    # امنیت ساده: اگر نوبت کاربر دارد ولی کاربر جاری لاگین نیست یا متفاوت است، جلوگیری کن
    if appointment.patient and appointment.patient != request.user:
         return render(request, 'payment/payment_failed.html', {'error_message': 'دسترسی غیرمجاز به نوبت.'})

    total_discount = appointment.points_discount_amount + appointment.code_discount_amount
    final_amount = appointment.get_total_price() - total_discount
    final_amount = max(0, int(final_amount))

    txn_obj, created = Transaction.objects.update_or_create(
        appointment=appointment,
        defaults={
            'amount': final_amount,
            'status': 'PENDING',
            'authority': None 
        }
    )

    # اتصال به زرین‌پال (کد قبلی بدون تغییر)
    client = ZarinPal(merchant_id=settings.ZARINPAL_MERCHANT_ID)
    client.sandbox = settings.DEBUG 
    
    # توضیحات برای درگاه
    desc_name = appointment.get_full_name()
    req_data = {
        "amount": final_amount,
        "callback_url": settings.ZARINPAL_CALLBACK_URL,
        "description": f"پرداخت نوبت {appointment.tracking_code} - {desc_name}"
    }
    
    try:
        res = client.request(req_data)
        if res and res.data and res.data.code == 100 and res.data.authority:
            txn_obj.authority = res.data.authority
            txn_obj.save(update_fields=['authority'])
            return redirect(f'https://sandbox.zarinpal.com/pg/StartPay/{res.data.authority}' if settings.DEBUG else f'https://www.zarinpal.com/pg/StartPay/{res.data.authority}')
        else:
            _handle_failed_payment(txn_obj)
            return render(request, 'payment/payment_failed.html', {'error_message': 'خطا در دریافت پاسخ از درگاه.'})
    except Exception as e:
        print(f"ZarinPal Request Error: {e}")
        _handle_failed_payment(txn_obj)
        return render(request, 'payment/payment_failed.html', {'error_message': 'خطای سیستمی.'})


def payment_callback_view(request: HttpRequest) -> HttpResponse:
    """
    بازگشت از درگاه.
    """
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')

    # حذف select_related('appointment__patient__profile') چون ممکن است بیمار None باشد
    # و باعث خطا شود. به جای آن در کد هندل می‌کنیم.
    txn_obj = get_object_or_404(Transaction.objects.select_related('appointment', 'appointment__discount_code'), authority=authority)
    
    if txn_obj.status == 'SUCCESS':
        return render(request, 'payment/payment_success.html', {'ref_id': 'Already Verified'})

    if status != 'OK':
        _handle_failed_payment(txn_obj)
        return render(request, 'payment/payment_failed.html', {'error_message': 'پرداخت لغو شد یا ناموفق بود.'})

    client = ZarinPal(merchant_id=settings.ZARINPAL_MERCHANT_ID)
    client.sandbox = settings.DEBUG

    verify_data = {
        "amount": int(txn_obj.amount), 
        "authority": authority
    }

    try:
        res = client.verify(verify_data)
        
        if res and res.data and res.data.code in [100, 101]:
            with db_transaction.atomic():
                txn_obj.status = 'SUCCESS'
                txn_obj.save(update_fields=['status'])
                
                appointment = txn_obj.appointment
                appointment.status = 'CONFIRMED'
                appointment.save(update_fields=['status'])
                
                # کسر امتیاز (فقط اگر بیمار عضو باشد و امتیاز خرج کرده باشد)
                # نکته: کسر امتیاز در ویوی create انجام شد، اینجا فقط تایید نهایی است
                # اما اگر منطق بازگشت امتیاز در صورت شکست دارید، اینجا مهم است.
                # در اینجا لاجیک قبلی شما چک می‌کرد. ما فقط شرط patient را اضافه می‌کنیم.
                if appointment.patient and appointment.points_used > 0:
                    # امتیاز قبلاً کسر شده بود؟ اگر نه اینجا کسر کنید.
                    # در ویوی create کسر کردیم. پس اینجا کاری نداریم مگر اینکه استراتژی فرق کند.
                    pass
                
                if appointment.discount_code and appointment.discount_code.is_one_time:
                    appointment.discount_code.is_used = True
                    appointment.discount_code.save(update_fields=['is_used'])
                
                _send_success_notifications(request, appointment, txn_obj)

                is_guest = appointment.patient is None
                earned_points = 0
                
                # محاسبه امتیاز (مثلا بر اساس مبلغ یا عدد ثابت ۵۰۰ برای خوش‌آمدگویی)
                if is_guest:
                    # مثلا ۵۰۰ امتیاز ثابت برای تبدیل مهمان به عضو
                    earned_points = 500

                if appointment.patient:
                    successful_txns = Transaction.objects.filter(
                        appointment__patient=appointment.patient, 
                        status='SUCCESS'
                    ).count()
                    
                    # چون این تراکنش الان ذخیره شده، اگر تعداد ۱ باشد یعنی خرید اول است
                    # (یا اگر لاجیک قبل از سیو باشد، تعداد ۰)
                    # اما چون txn_obj.status = 'SUCCESS' را چند خط بالاتر زدیم، تعداد باید ۱ باشد.
                    if successful_txns == 1:
                        referrer = appointment.patient.profile.referred_by
                        if referrer:
                            # اعطای ۵۰۰۰ امتیاز (۵۰ هزار تومان) به معرف
                            referrer.profile.points += 5000 
                            referrer.profile.save()
                            
                            # ارسال نوتیفیکیشن به معرف
                            Notification.objects.create(
                                user=referrer,
                                message=f"تبریک! دوست شما {appointment.patient.first_name} اولین خریدش را انجام داد. ۵۰۰۰ امتیاز به شما تعلق گرفت."
                            )   

            return render(request, 'payment/payment_success.html', {
                'ref_id': res.data.ref_id,
                'tracking_code': appointment.tracking_code,
                # ارسال متغیرهای جدید به تمپلیت
                'is_guest': is_guest,
                'appointment_id': appointment.id,
                'earned_points': earned_points
            })
        
        else:
            _handle_failed_payment(txn_obj)
            return render(request, 'payment/payment_failed.html')

    except Exception as e:
        print(f"Verify Error: {e}")
        _handle_failed_payment(txn_obj)
        return render(request, 'payment/payment_failed.html')

def _handle_failed_payment(transaction):
    transaction.status = 'FAILED'
    transaction.save(update_fields=['status'])
    if transaction.appointment.status == 'PENDING':
        transaction.appointment.status = 'CANCELED'
        transaction.appointment.save(update_fields=['status'])
        
        # اگر امتیاز کسر شده بود، برگردانیم
        appt = transaction.appointment
        if appt.patient and appt.points_used > 0:
            appt.patient.profile.points += appt.points_used
            appt.patient.profile.save()

def _send_success_notifications(request, appointment, transaction):
    staff_users = CustomUser.objects.filter(is_staff=True)
    if staff_users.exists():
        name = appointment.get_full_name()
        link = request.build_absolute_uri(reverse('reception_panel:appointment_list'))
        notifications = [
            Notification(
                user=staff,
                message=f"پرداخت موفق: {name} (کد: {appointment.tracking_code})",
                link=link
            ) for staff in staff_users
        ]
        Notification.objects.bulk_create(notifications)