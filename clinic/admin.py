# clinic/admin.py
"""
تنظیمات پنل ادمین جنگو برای اپلیکیشن clinic.
بهینه‌سازی شده با list_select_related برای کاهش تعداد کوئری‌ها.
"""

from django.contrib import admin
from django import forms
from django.db.models import QuerySet
from django.http import HttpRequest
from .models import (
    Service, PortfolioItem, FAQ, Testimonial, 
    DiscountCode, ServiceGroup, Device, WorkHours
)
from jalali_date.admin import ModelAdminJalaliMixin

class WorkHoursInline(admin.TabularInline):
    """
    مدیریت ساعات کاری به صورت Inline.
    """
    model = WorkHours
    extra = 1
    verbose_name = "ساعت کاری"
    verbose_name_plural = "ساعات کاری"
    fields = ('day_of_week', 'start_time', 'end_time', 'gender_specific', 'service_group', 'service')

    def get_formset(self, request, obj=None, **kwargs):
        """
        شخصی‌سازی فرم‌ست برای پنهان کردن فیلدهای اضافی بر اساس کانتکست والد.
        """
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            if isinstance(obj, ServiceGroup):
                # در صفحه گروه خدماتی: فیلد سرویس را مخفی کن
                formset.form.base_fields['service_group'].initial = obj.id
                formset.form.base_fields['service'].widget = forms.HiddenInput()
                formset.form.base_fields['service'].required = False
            elif isinstance(obj, Service):
                # در صفحه خدمت: فیلد گروه را مخفی کن
                formset.form.base_fields['service'].initial = obj.id
                formset.form.base_fields['service_group'].widget = forms.HiddenInput()
                formset.form.base_fields['service_group'].required = False
        return formset

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    verbose_name = "خدمت"
    verbose_name_plural = "خدمات (زیرگروه‌ها)"

@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'allow_multiple_selection', 'has_devices')
    search_fields = ('name',)
    inlines = [ServiceInline, WorkHoursInline]
    filter_horizontal = ('available_devices',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'duration', 'price', 'badge')
    search_fields = ('name', 'group__name')
    list_filter = ('group', 'badge')
    # بهینه‌سازی: دریافت اطلاعات گروه با یک کوئری
    list_select_related = ('group',)
    inlines = [WorkHoursInline]

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'service', 'created_at')
    list_filter = ('service__group', 'service') # فیلتر بر اساس گروه سرویس هم مفید است
    search_fields = ('title', 'description')
    # بهینه‌سازی: دریافت سرویس مرتبط
    list_select_related = ('service',)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'sort_order', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('question', 'answer')
    list_editable = ('sort_order', 'is_active') # ویرایش سریع اولویت و وضعیت
    list_select_related = ('category',) # بهینه‌سازی کوئری

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'service', 'rating', 'created_at')
    list_filter = ('service', 'rating')
    search_fields = ('patient_name', 'comment')
    raw_id_fields = ('service',)
    list_select_related = ('service',)

@admin.register(DiscountCode)
class DiscountCodeAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = (
        'code', 'discount_type', 'value', 
        'start_date', 'end_date', 
        'is_active', 'user', 'is_one_time', 'is_used'
    )
    list_filter = ('is_active', 'discount_type', 'is_one_time', 'is_used')
    search_fields = ('code', 'user__username', 'user__phone_number')
    raw_id_fields = ('user',)
    list_select_related = ('user',)