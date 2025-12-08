# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# دقت کنید: در اینجا فقط فرم‌های پروفایل ایمپورت شده‌اند، نه فرم ثبت‌نام
from .forms import UserEditForm, ProfileEditForm 
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