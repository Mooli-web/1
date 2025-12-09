# users/views.py
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# دقت کنید: در اینجا فقط فرم‌های پروفایل ایمپورت شده‌اند، نه فرم ثبت‌نام
from .forms import UserEditForm, ProfileEditForm 
from .models import CustomUser, Profile
from booking.models import Appointment
from payment.models import Transaction
from reception_panel.models import Notification

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
            # 1. یافتن نوبت
            appointment = Appointment.objects.select_for_update().get(id=appointment_id)
            
            if appointment.patient:
                return JsonResponse({'status': 'error', 'message': 'این نوبت قبلاً به یک کاربر متصل شده است.'}, status=400)
            
            phone = appointment.guest_phone_number
            if not phone:
                return JsonResponse({'status': 'error', 'message': 'شماره تماس در نوبت یافت نشد.'}, status=400)

            # 2. ایجاد یا یافتن کاربر (اگر قبلا ثبت نام کرده ولی لاگین نکرده بود)
            user, created = CustomUser.objects.get_or_create(
                phone_number=phone,
                defaults={
                    'username': phone, # نام کاربری همان شماره موبایل
                    'first_name': appointment.guest_first_name,
                    'last_name': appointment.guest_last_name,
                    'role': CustomUser.Role.PATIENT
                }
            )
            
            # تنظیم رمز عبور
            user.set_password(password)
            user.save()
            
            # اطمینان از وجود پروفایل
            Profile.objects.get_or_create(user=user)
            
            # 3. اتصال نوبت به کاربر
            appointment.patient = user
            appointment.save()
            
            # 4. اعطای امتیاز (مثلا 500 امتیاز جایزه)
            user.profile.points += 500
            user.profile.save()
            
            # 5. لاگین خودکار کاربر
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            return JsonResponse({
                'status': 'success', 
                'message': 'تبریک! حساب شما ساخته شد و ۵۰۰ امتیاز دریافت کردید.'
            })

    except Appointment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'نوبت یافت نشد.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)