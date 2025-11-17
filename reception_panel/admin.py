from django.contrib import admin
# --- ADDED: Import Notification model ---
from .models import Notification
from jalali_date.admin import ModelAdminJalaliMixin # <-- اضافه شد

# --- ADDED: Register Notification model ---
@admin.register(Notification)
class NotificationAdmin(ModelAdminJalaliMixin, admin.ModelAdmin): # <-- اصلاح شد
    list_display = ('user', 'message', 'is_read', 'created_at', 'link')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    raw_id_fields = ('user',)
    list_editable = ('is_read',)