# a_copy/clinic/admin.py

from django.contrib import admin
# --- ADDED: Import forms for HiddenInput ---
from django import forms 
from .models import (
    Service, PortfolioItem, FAQ, Testimonial, 
    DiscountCode, ServiceGroup, Device, WorkHours
)
# --- ADDED: Import for Jalali Admin ---
from jalali_date.admin import ModelAdminJalaliMixin


class WorkHoursInline(admin.TabularInline):
    model = WorkHours
    extra = 1
    verbose_name = "ساعت کاری"
    verbose_name_plural = "ساعات کاری"
    # --- TASK 9: Explicitly add fields ---
    fields = ('day_of_week', 'start_time', 'end_time', 'gender_specific', 'service_group', 'service')

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # obj is the instance of ServiceGroup or Service being edited
        if obj:
            if isinstance(obj, ServiceGroup):
                # 1. Set the initial value for new rows to this ServiceGroup
                formset.form.base_fields['service_group'].initial = obj.id
                # 2. Hide the 'service' field
                # --- FIXED: Use forms.HiddenInput ---
                formset.form.base_fields['service'].widget = forms.HiddenInput()
            elif isinstance(obj, Service):
                # 1. Set the initial value for new rows to this Service
                formset.form.base_fields['service'].initial = obj.id
                # 2. Hide the 'service_group' field
                # --- FIXED: Use forms.HiddenInput ---
                formset.form.base_fields['service_group'].widget = forms.HiddenInput()
        return formset


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    verbose_name = "خدمت"
    verbose_name_plural = "خدمات"

@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    # --- MODIFIED: Added 'home_page_image' to list_display ---
    list_display = ('name', 'home_page_image', 'allow_multiple_selection', 'has_devices')
    search_fields = ('name',)
    inlines = [ServiceInline, WorkHoursInline]
    filter_horizontal = ('available_devices',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'duration', 'price')
    search_fields = ('name', 'group__name')
    list_filter = ('group',)
    inlines = [WorkHoursInline]


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'service', 'created_at')
    list_filter = ('service',)
    search_fields = ('title', 'description')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('question', 'answer')

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'service', 'rating', 'created_at')
    list_filter = ('service', 'rating')
    search_fields = ('patient_name', 'comment')
    raw_id_fields = ('service',)

# --- MODIFIED: Added ModelAdminJalaliMixin ---
@admin.register(DiscountCode)
class DiscountCodeAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'start_date', 'end_date', 'is_active', 'user', 'is_one_time', 'is_used')
    list_filter = ('is_active', 'discount_type', 'is_one_time', 'is_used', 'user')
    search_fields = ('code', 'user__username')
    raw_id_fields = ('user',)