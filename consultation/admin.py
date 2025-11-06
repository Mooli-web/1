# a_copy/consultation/admin.py

from django.contrib import admin
from .models import ConsultationRequest, ConsultationMessage

class ConsultationMessageInline(admin.TabularInline):
    model = ConsultationMessage
    extra = 0
    readonly_fields = ('user', 'message', 'timestamp')
    verbose_name = "پیام"
    verbose_name_plural = "پیام‌ها"

class ConsultationRequestAdmin(admin.ModelAdmin):
    # --- TASK 3: Translate fields ---
    list_display = ('subject', 'patient', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject', 'patient__username')
    raw_id_fields = ('patient',)
    inlines = [ConsultationMessageInline]

admin.site.register(ConsultationRequest, ConsultationRequestAdmin)
# admin.site.register(ConsultationMessage) # Registered via inline