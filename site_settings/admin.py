from django.contrib import admin
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('price_to_points_rate',)
    
    def has_add_permission(self, request):
        # جلوگیری از ایجاد نمونه جدید (چون Singleton است)
        return False

    def has_delete_permission(self, request, obj=None):
        # جلوگیری از حذف نمونه
        return False