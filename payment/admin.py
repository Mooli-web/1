# a_copy/payment/admin.py

from django.contrib import admin
from .models import Transaction

# --- TASK 3: Register Transaction model with Farsi admin ---
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'amount', 'status', 'created_at', 'authority')
    list_filter = ('status', 'created_at')
    search_fields = ('appointment__patient__username', 'authority')
    raw_id_fields = ('appointment',)
    readonly_fields = ('amount', 'authority', 'created_at', 'appointment')

    # Make all fields read-only
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False