# users/views.py
"""
ویوهای مربوط به بخش کاربری (عمومی).
- SignUpView: صفحه ثبت‌نام.
- dashboard_view: داشبورد اصلی بیمار (نمایش نوبت‌ها، امتیازات و ...).
- profile_update_view: صفحه ویرایش پروفایل توسط بیمار.
- APIهای داخلی کاربر (مانند خواندن اعلان‌ها).
"""

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, UserEditForm, ProfileEditForm
from booking.models import Appointment
from payment.models import Transaction
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from reception_panel.models import Notification  # مدل اعلان‌ها


class SignUpView(CreateView):
    """
    ویو مبتنی بر کلاس (Class-Based View) برای صفحه ثبت‌نام.
    از فرم CustomUserCreationForm استفاده می‌کند.
    """
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')  # هدایت به صفحه لاگین پس از ثبت‌نام موفق

    def form_valid(self, form):
        """
        پس از اعتبارسنجی فرم، کاربر را بلافاصله "فعال" می‌کند.
        """
        user = form.save(commit=False)
        user.is_active = True  # کاربر بلافاصله پس از ثبت‌نام فعال می‌شود
        user.save()
        return super().form_valid(form)

# این خط برای اتصال ویو مبتنی بر کلاس به urls.py ضروری است
signup_view = SignUpView.as_view()


@login_required  # کاربر برای مشاهده داشبورد باید لاگین باشد
def dashboard_view(request):
    """
    ویو داشبورد اصلی بیمار.
    اطلاعات کلیدی بیمار شامل نوبت‌ها، تراکنش‌ها و امتیازات را نمایش می‌دهد.
    """
    
    # --- بهینه‌سازی کوئری نوبت‌ها ---
    # نوبت‌های "انجام شده" که منتظر "امتیازدهی" هستند جداگانه واکشی می‌شوند
    unrated_appointments = Appointment.objects.filter(
        patient=request.user, 
        status='DONE', 
        is_rated=False
    ).prefetch_related('services').order_by('-start_time')
    
    # سایر نوبت‌ها (فعال، لغو شده، یا امتیاز داده شده)
    other_appointments = Appointment.objects.filter(
        patient=request.user
    ).exclude(
        status='DONE', 
        is_rated=False
    ).prefetch_related('services').order_by('-start_time')
    
    # واکشی تراکنش‌های کاربر
    user_transactions = Transaction.objects.filter(
        appointment__patient=request.user
    ).select_related('appointment').prefetch_related('appointment__services').order_by('-created_at')
    
    user_points = request.user.profile.points
    
    context = {
        'unrated_appointments': unrated_appointments,
        'other_appointments': other_appointments,
        'transactions': user_transactions,
        'user_points': user_points,
    }
    return render(request, 'users/dashboard.html', context)


@login_required
def profile_update_view(request):
    """
    ویو صفحه "ویرایش پروفایل" توسط خود کاربر.
    این ویو همزمان دو فرم (UserEditForm و ProfileEditForm) را مدیریت می‌کند.
    """
    if request.method == 'POST':
        u_form = UserEditForm(request.POST, instance=request.user)
        p_form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
            return redirect('users:profile_update')  # بازگشت به همین صفحه
    else:
        # حالت GET: نمایش فرم‌های پر شده با اطلاعات فعلی
        u_form = UserEditForm(instance=request.user)
        p_form = ProfileEditForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/profile_update.html', context)


@require_POST
@login_required
def mark_notifications_as_read_api(request):
    """
    API داخلی برای علامت‌گذاری اعلان‌های "بیمار" به عنوان خوانده شده.
    (مشابه API در پنل پذیرش، اما مخصوص کاربر لاگین کرده)
    """
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)