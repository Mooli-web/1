from django.contrib import admin
# --- ADDED: Import Notification model ---
from .models import Notification

# --- ADDED: Register Notification model ---
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at', 'link')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    raw_id_fields = ('user',)
    list_editable = ('is_read',)