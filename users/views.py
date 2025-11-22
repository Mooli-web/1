# users/views.py
"""
ویوهای سمت کاربر (ثبت‌نام، داشبورد، پروفایل).
"""

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Prefetch

from .forms import CustomUserCreationForm, UserEditForm, ProfileEditForm
from booking.models import Appointment
from payment.models import Transaction
from reception_panel.models import Notification

class SignUpView(CreateView):
    """ثبت‌نام کاربر جدید."""
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        messages.success(self.request, "ثبت‌نام با موفقیت انجام شد. وارد شوید.")
        return super().form_valid(form)

@login_required
def dashboard_view(request):
    """
    داشبورد کاربر.
    اصلاح شده: ارسال لیست کامل نوبت‌ها با نام 'appointments' برای تمپلیت.
    """
    user = request.user
    
    # 1. دریافت تمام نوبت‌ها برای نمایش در جدول اصلی (رفع باگ عدم نمایش)
    all_appointments = Appointment.objects.filter(patient=user).select_related(
        'selected_device', 'discount_code'
    ).prefetch_related('services').order_by('-start_time')

    # 2. جدا کردن نوبت‌های نیازمند نظردهی (برای بخش هشدار یا استفاده‌های خاص)
    unrated_appointments = all_appointments.filter(status='DONE', is_rated=False)
    
    # 3. تراکنش‌ها
    user_transactions = Transaction.objects.filter(
        appointment__patient=user
    ).select_related('appointment').order_by('-created_at')
    
    context = {
        'appointments': all_appointments, # <-- این خط حیاتی است (تمپلیت این را می‌خواند)
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