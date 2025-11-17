# payment/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن payment.
"""

from django.contrib import admin
from .models import Transaction  # <-- مهم: مدل از اینجا "وارد" (import) می‌شود
from jalali_date.admin import ModelAdminJalaliMixin # <-- اضافه شد

@admin.register(Transaction)
class TransactionAdmin(ModelAdminJalaliMixin, admin.ModelAdmin): # <-- اصلاح شد
    """
    کلاس مدیریتی برای نمایش تراکنش‌ها در پنل ادمین.
    تراکنش‌ها در ادمین "فقط خواندنی" (Read-Only) هستند.
    
    (این کلاس TransactionAdmin است و نباید با مدل Transaction اشتباه گرفته شود)
    """
    
    list_display = ('appointment', 'amount', 'status', 'created_at', 'authority')
    list_filter = ('status', 'created_at')
    search_fields = ('appointment__patient__username', 'authority')
    raw_id_fields = ('appointment',)
    
    # تعریف فیلدهای فقط خواندنی (برای نمایش در صفحه ویرایش)
    readonly_fields = ('appointment', 'amount', 'status', 'created_at', 'authority')

    # --- جلوگیری از هرگونه تغییر دستی ---
    
    def has_add_permission(self, request):
        # جلوگیری از ایجاد تراکنش دستی
        return False

    def has_change_permission(self, request, obj=None):
        # جلوگیری از ویرایش تراکنش دستی
        return False
        
    def has_delete_permission(self, request, obj=None):
        # جلوگیری از حذف تراکنش دستی
        return False