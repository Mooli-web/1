# a_copy/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(UserAdmin):
    # --- MODIFIED: Added 'gender' to list_display ---
    list_display = ('username', 'email', 'phone_number', 'first_name', 'last_name', 'gender', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        # --- MODIFIED: Added 'gender' to fieldsets (for editing in admin) ---
        (_('فیلدهای سفارشی'), {'fields': ('role', 'phone_number', 'gender')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        # --- MODIFIED: Added 'gender' to add_fieldsets ---
        (_('فیلدهای سفارشی'), {'fields': ('role', 'phone_number', 'first_name', 'last_name', 'email', 'gender')}),
    )
    search_fields = ('username', 'first_name', 'last_name', 'phone_number', 'email')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'gender') # --- ADDED: 'gender' to filter

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'points')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)