# users/views.py
import json
import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# ایمپورت فرم‌ها و مدل‌ها
from .forms import UserEditForm, ProfileEditForm
from .allauth_forms import AllauthSignupForm  # فرم ثبت‌نام که اصلاح کردیم
from .models import CustomUser, Profile
from booking.models import Appointment
from payment.models import Transaction
from reception_panel.models import Notification
from .utils import send_otp_sms  # تابعی که برای ارسال پیامک ساختید

@login_required
def dashboard_view(request):
    """داشبورد کاربر."""
    user = request.user
    
    all_appointments = Appointment.objects.filter(patient=user).select_related(
        'selected_device', 'discount_code'
    ).prefetch_related('services').order_by('-start_time')

    unrated_appointments = all_appointments.filter(status='DONE', is_rated=False)
    
    user_transactions = Transaction.objects.filter(
        appointment__patient=user
    ).select_related('appointment').order_by('-created_at')
    
    context = {
        'appointments': all_appointments,
        'unrated_appointments': unrated_appointments,
        'transactions': user_transactions,
        'user_points': user.profile.points,
    }
    return render(request, 'users/dashboard.html', context)

@login_required
def profile_update_view(request):
    """ویرایش اطلاعات کاربری و پروفایل."""
    if request.method == 'POST':
        u_form = UserEditForm(request.POST, instance=request.user)
        p_form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'پروفایل شما به‌روزرسانی شد.')
            return redirect('users:profile_update')
    else:
        u_form = UserEditForm(instance=request.user)
        p_form = ProfileEditForm(instance=request.user.profile)

    return render(request, 'users/profile_update.html', {'u_form': u_form, 'p_form': p_form})

@require_POST
@login_required
def mark_notifications_as_read_api(request):
    """API خواندن اعلان‌ها."""
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@require_POST
def claim_guest_points_api(request):
    """
    تبدیل کاربر مهمان به عضو دائم و اعطای امتیاز.
    """
    try:
        data = json.loads(request.body)
        appointment_id = data.get('appointment_id')
        password = data.get('password')
        
        if not appointment_id or not password:
            return JsonResponse({'status': 'error', 'message': 'اطلاعات ناقص است.'}, status=400)
            
        if len(password) < 5:
             return JsonResponse({'status': 'error', 'message': 'رمز عبور باید حداقل ۵ کاراکتر باشد.'}, status=400)

        with transaction.atomic():
            appointment = Appointment.objects.select_for_update().get(id=appointment_id)
            
            if appointment.patient:
                return JsonResponse({'status': 'error', 'message': 'این نوبت قبلاً به یک کاربر متصل شده است.'}, status=400)
            
            phone = appointment.guest_phone_number
            if not phone:
                return JsonResponse({'status': 'error', 'message': 'شماره تماس در نوبت یافت نشد.'}, status=400)

            user, created = CustomUser.objects.get_or_create(
                phone_number=phone,
                defaults={
                    'username': phone,
                    'first_name': appointment.guest_first_name,
                    'last_name': appointment.guest_last_name,
                    'role': CustomUser.Role.PATIENT
                }
            )
            
            user.set_password(password)
            user.save()
            
            Profile.objects.get_or_create(user=user)
            
            appointment.patient = user
            appointment.save()
            
            user.profile.points += 500
            user.profile.save()
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            return JsonResponse({
                'status': 'success', 
                'message': 'تبریک! حساب شما ساخته شد و ۵۰۰ امتیاز دریافت کردید.'
            })

    except Appointment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'نوبت یافت نشد.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# -------------------------------------------------------------------------
# بخش‌های جدید اضافه شده برای ثبت‌نام پیامکی (OTP)
# -------------------------------------------------------------------------

def signup_view(request):
    """
    مرحله اول ثبت‌نام: دریافت اطلاعات و ارسال کد تایید.
    """
    if request.user.is_authenticated:
        return redirect('users:dashboard')

    if request.method == 'POST':
        form = AllauthSignupForm(request.POST)
        # اعتبارسنجی‌ها (شامل چک کردن تکراری نبودن شماره و فرمت صحیح) اجرا می‌شود
        if form.is_valid():
            # 1. ذخیره موقت اطلاعات در سشن (هنوز کاربر ساخته نمی‌شود)
            # از cleaned_data استفاده می‌کنیم تا داده‌های تمیز شده (مثل اعداد انگلیسی) را بگیریم
            request.session['signup_data'] = form.cleaned_data
            
            # 2. تولید کد تایید ۵ رقمی
            otp_code = str(random.randint(10000, 99999))
            print(f"-----> کد تایید شما: {otp_code} <-----")
            request.session['otp_code'] = otp_code
            
            # 3. ارسال پیامک
            phone = form.cleaned_data['phone_number']
            
            # تلاش برای ارسال پیامک
            sms_status = send_otp_sms(phone, otp_code)
            
            # اگر پیامک رفت که عالی، اگر نرفت هم (چون داریم تست میکنیم) اجازه بده بریم مرحله بعد
            # در نسخه نهایی (Production) این شرط باید سخت‌گیرانه باشد
            if sms_status:
                messages.success(request, f'کد تایید به شماره {phone} ارسال شد.')
            else:
                # پیام برای آگاهی شما در حالت تست
                messages.warning(request, 'پیامک ارسال نشد (حالت تست: کد در ترمینال چاپ شده است).')
                print(f"DEBUG: Mock SMS sent to {phone}: {otp_code}")

            # در هر صورت ریدایرکت کن
            return redirect('users:verify_otp')
    else:
        form = AllauthSignupForm()
    
    return render(request, 'account/signup.html', {'form': form})

def verify_otp_view(request):
    """
    مرحله دوم ثبت‌نام: بررسی کد تایید و ساخت کاربر.
    """
    # اگر اطلاعاتی در سشن نیست، یعنی کاربر بدون طی کردن مرحله اول به اینجا آمده
    if 'signup_data' not in request.session or 'otp_code' not in request.session:
        messages.error(request, 'اطلاعات یافت نشد. لطفاً از ابتدا ثبت‌نام کنید.')
        return redirect('users:signup_otp')

    if request.method == 'POST':
        user_code = request.POST.get('code')
        session_code = request.session.get('otp_code')
        
        if user_code == session_code:
            # --- کد صحیح است: ساخت نهایی کاربر در دیتابیس ---
            data = request.session['signup_data']
            
            try:
                with transaction.atomic():
                    # ایجاد کاربر
                    user = CustomUser.objects.create_user(
                        username=data['phone_number'], # نام کاربری همان شماره موبایل
                        phone_number=data['phone_number'],
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        gender=data['gender'],
                        role=CustomUser.Role.PATIENT,
                        password=None # در اینجا پسورد ست نمی‌شود (کاربر با OTP لاگین می‌کند)
                    )
                    
                    # اگر کد معرف داشت
                    ref_code = data.get('referral_code')
                    if ref_code:
                        try:
                            referrer = Profile.objects.get(referral_code__iexact=ref_code).user
                            user.profile.referred_by = referrer
                            user.profile.save()
                        except Profile.DoesNotExist:
                            pass

                    # لاگین کردن کاربر
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    
                    # پاک کردن اطلاعات موقت از سشن
                    del request.session['signup_data']
                    del request.session['otp_code']
                    
                    messages.success(request, 'حساب کاربری شما با موفقیت ساخته شد.')
                    return redirect('users:dashboard')
                    
            except Exception as e:
                messages.error(request, f'خطا در ساخت کاربر: {e}')
                return redirect('users:signup_otp')
        else:
            messages.error(request, 'کد تایید اشتباه است.')

    return render(request, 'users/verify_otp.html')