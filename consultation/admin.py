# consultation/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن consultation.
"""

from django.contrib import admin
from .models import ConsultationRequest, ConsultationMessage

class ConsultationMessageInline(admin.TabularInline):
    """
    نمایش پیام‌های چت به صورت ردیفی (Inline) در صفحه
    "درخواست مشاوره" (فقط در ادمین).
    """
    model = ConsultationMessage
    extra = 0  # هیچ ردیف خالی جدیدی نمایش نده
    # پیام‌ها در ادمین فقط خواندنی هستند (برای جلوگیری از دستکاری)
    readonly_fields = ('user', 'message', 'timestamp')
    verbose_name = "پیام"
    verbose_name_plural = "پیام‌ها"

@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    """
    کلاس مدیریتی برای "درخواست مشاوره" در پنل ادمین.
    """
    list_display = ('subject', 'patient', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject', 'patient__username')
    raw_id_fields = ('patient',)
    # نمایش پیام‌ها در داخل صفحه درخواست
    inlines = [ConsultationMessageInline]

# مدل ConsultationMessage به صورت مستقیم ثبت نمی‌شود،
# زیرا از طریق Inline در بالا مدیریت می‌شود.
# admin.site.register(ConsultationMessage)