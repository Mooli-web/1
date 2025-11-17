# users/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن users.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile
from django.utils.translation import gettext_lazy as _
from jalali_date.admin import ModelAdminJalaliMixin # <-- اضافه شد

class CustomUserAdmin(ModelAdminJalaliMixin, UserAdmin): # <-- اصلاح شد
    """
    سفارشی‌سازی نمایش CustomUser در پنل ادمین.
    فیلدهای سفارشی (role, phone_number, gender) را به پنل ادمین
    اضافه می‌کند.
    """
    
    list_display = (
        'username', 
        'email', 
        'phone_number', 
        'first_name', 
        'last_name', 
        'gender',  # فیلد سفارشی
        'is_staff',
        'date_joined', # <-- اضافه کردن تاریخ عضویت به لیست
    )
    
    # فیلدهایی که در صفحه "ویرایش" کاربر در ادمین نمایش داده می‌شوند
    fieldsets = UserAdmin.fieldsets + (
        (_('فیلدهای سفارشی'), {'fields': ('role', 'phone_number', 'gender')}),
    )
    
    # فیلدهایی که در صفحه "ایجاد" کاربر جدید در ادمین نمایش داده می‌شوند
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('فیلدهای سفارشی'), {'fields': ('role', 'phone_number', 'first_name', 'last_name', 'email', 'gender')}),
    )
    
    search_fields = ('username', 'first_name', 'last_name', 'phone_number', 'email')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'gender', 'date_joined') # <-- date_joined اضافه شد
    
    # اضافه کردن فیلتر تاریخ شمسی
    date_hierarchy = 'date_joined'

# ثبت مدل CustomUser با کلاس ادمین سفارشی
admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    تنظیمات نمایش Profile در پنل ادمین.
    """
    list_display = ('user', 'points')
    search_fields = ('user__username',)
    # استفاده از raw_id_fields برای جستجوی آسان کاربر (به جای dropdown)
    raw_id_fields = ('user',)