# a_copy/users/views.py

from django.shortcuts import render, redirect # <-- redirect ADDED
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, UserEditForm, ProfileEditForm # <-- Forms ADDED
from booking.models import Appointment
from payment.models import Transaction
from django.contrib import messages # <-- messages ADDED
# --- TASK 4: Imports for API ---
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from reception_panel.models import Notification # (ایمپورت مدل نوتیفیکیشن)


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True # The user is activated immediately
        user.save()
        return super().form_valid(form)

# --- THIS LINE WAS MISSING ---
signup_view = SignUpView.as_view()

@login_required
def dashboard_view(request):
    # --- TASK 5: Split appointments query ---
    unrated_appointments = Appointment.objects.filter(
        patient=request.user, 
        status='DONE', 
        is_rated=False
    ).prefetch_related('services').order_by('-start_time')
    
    other_appointments = Appointment.objects.filter(
        patient=request.user
    ).exclude(
        status='DONE', 
        is_rated=False
    ).prefetch_related('services').order_by('-start_time')
    
    # --- OPTIMIZED: Changed query for nested M2M ---
    user_transactions = Transaction.objects.filter(appointment__patient=request.user).select_related(
        'appointment'
    ).prefetch_related('appointment__services').order_by('-created_at')
    
    user_points = request.user.profile.points
    
    context = {
        # 'appointments': user_appointments, # <-- Replaced by TASK 5
        'unrated_appointments': unrated_appointments,
        'other_appointments': other_appointments,
        'transactions': user_transactions,
        'user_points': user_points,
    }
    return render(request, 'users/dashboard.html', context)

# --- ADDED: View for users to edit their profile ---
@login_required
def profile_update_view(request):
    if request.method == 'POST':
        u_form = UserEditForm(request.POST, instance=request.user)
        p_form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
            return redirect('users:profile_update') # Redirect back to the same page
    else:
        u_form = UserEditForm(instance=request.user)
        p_form = ProfileEditForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/profile_update.html', context)

# --- TASK 4: API to mark notifications as read (Patient) ---
@require_POST
@login_required
def mark_notifications_as_read_api(request):
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)