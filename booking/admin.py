# a_copy/booking/admin.py

from django.contrib import admin
# --- REMOVED: settings import ---
from .models import Appointment
# --- ADDED: Import for Jalali Admin ---
from jalali_date.admin import ModelAdminJalaliMixin
# --- TASK 2: Import SiteSettings ---
from site_settings.models import SiteSettings


def mark_as_done_and_award_points(modeladmin, request, queryset):
    # --- TASK 2: Get rate from SiteSettings ---
    try:
        # get_or_create ensures it exists, [0] gets the object
        rate = SiteSettings.objects.get_or_create(pk=1)[0].price_to_points_rate
    except Exception:
        rate = 0 # Fail safe, no points awarded if setting fails
    
    # --- TASK 2: Filter for correct status and points_awarded=False ---
    for appointment in queryset.filter(status='CONFIRMED', points_awarded=False):
        # --- TASK 2: Set flag ---
        appointment.status = 'DONE'
        appointment.points_awarded = True 
        appointment.save()
        
        # --- BUG 2 FIX: Calculate points based on paid amount ---
        try:
            # Check if transaction exists, was successful, and has a valid rate
            if rate > 0 and hasattr(appointment, 'transaction') and \
               appointment.transaction.status == 'SUCCESS' and \
               appointment.transaction.amount > 0:
                
                # Calculate points based on the actual amount paid
                points_to_award = int(appointment.transaction.amount / rate)
                
                if points_to_award > 0:
                    appointment.patient.profile.points += points_to_award
                    appointment.patient.profile.save()
                    
        except Exception: 
            # If transaction doesn't exist or any other error, just skip points
            pass 
        # --- END BUG 2 FIX ---

# --- TASK 3: Translate short_description ---
mark_as_done_and_award_points.short_description = "علامت‌گذاری به عنوان 'انجام شده' و اعطای امتیاز"

# --- MODIFIED: Added ModelAdminJalaliMixin ---
@admin.register(Appointment)
class AppointmentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    # --- TASK 3: Translate fields ---
    list_display = ('patient', 'get_services_display', 'start_time', 'status', 'selected_device', 'points_awarded') # TASK 2: Added 'points_awarded'
    list_filter = ('status', 'start_time', 'selected_device', 'points_awarded') # TASK 2: Added 'points_awarded'
    search_fields = ('patient__username', 'services__name')
    actions = [mark_as_done_and_award_points]
    
    # --- TASK 3: Translate readonly_fields ---
    readonly_fields = ('get_services_display',)
    list_per_page = 20
    raw_id_fields = ('patient', 'discount_code', 'selected_device')

    # Override get_services_display to work in readonly_fields
    def get_services_display(self, obj):
        return obj.get_services_display()
    get_services_display.short_description = "خدمات"
