# users/admin.py
"""
تنظیمات پنل ادمین برای اپلیکیشن users.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from jalali_date.admin import ModelAdminJalaliMixin
from .models import CustomUser, Profile

class CustomUserAdmin(ModelAdminJalaliMixin, UserAdmin):
    """
    مدیریت کاربران در ادمین.
    افزودن فیلدهای سفارشی (شماره تلفن، نقش، جنسیت) به فرم‌های ادمین.
    """
    list_display = (
        'username', 
        'phone_number', 
        'first_name', 
        'last_name', 
        'role', 
        'is_staff',
        'date_joined_display' # استفاده از تاریخ شمسی
    )
    
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'gender')
    search_fields = ('username', 'first_name', 'last_name', 'phone_number', 'email')
    ordering = ('-date_joined',)

    # فیلدست‌های ویرایش کاربر
    fieldsets = UserAdmin.fieldsets + (
        (_('اطلاعات تکمیلی'), {'fields': ('role', 'phone_number', 'gender')}),
    )
    
    # فیلدست‌های ایجاد کاربر
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('اطلاعات تکمیلی'), {
            'classes': ('wide',),
            'fields': ('role', 'phone_number', 'first_name', 'last_name', 'email', 'gender'),
        }),
    )

    def date_joined_display(self, obj):
        return obj.date_joined
    date_joined_display.short_description = _("تاریخ عضویت")

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    مدیریت پروفایل کاربران.
    """
    list_display = ('user', 'points_display')
    search_fields = ('user__username', 'user__phone_number')
    autocomplete_fields = ['user'] # جستجوی سریع برای لیست‌های طولانی
    
    def points_display(self, obj):
        return f"{obj.points:,} امتیاز"
    points_display.short_description = _("امتیاز")