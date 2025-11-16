# clinic/admin.py
"""
تنظیمات پنل ادمین جنگو برای مدل‌های اپلیکیشن clinic.
"""

from django.contrib import admin
from django import forms  # برای استفاده از HiddenInput
from .models import (
    Service, PortfolioItem, FAQ, Testimonial, 
    DiscountCode, ServiceGroup, Device, WorkHours
)
from jalali_date.admin import ModelAdminJaliMixin  # برای تقویم شمسی


class WorkHoursInline(admin.TabularInline):
    """
    نمایش فرم‌های "ساعات کاری" به صورت ردیفی (Inline)
    در داخل صفحات "گروه خدماتی" و "خدمت".
    """
    model = WorkHours
    extra = 1  # نمایش یک ردیف خالی برای افزودن
    verbose_name = "ساعت کاری"
    verbose_name_plural = "ساعات کاری"
    
    # فیلدهایی که در فرم اینلاین نمایش داده می‌شوند
    fields = ('day_of_week', 'start_time', 'end_time', 'gender_specific', 'service_group', 'service')

    def get_formset(self, request, obj=None, **kwargs):
        """
        بازنویسی (Override) متد get_formset برای یک تجربه کاربری بهتر:
        - اگر در صفحه "گروه خدماتی" هستیم، فیلد 'service_group' را مخفی
          و به صورت خودکار با گروه فعلی پر می‌کند.
        - اگر در صفحه "خدمت" هستیم، فیلد 'service' را مخفی
          و به صورت خودکار با خدمت فعلی پر می‌کند.
        """
        formset = super().get_formset(request, obj, **kwargs)
        if obj:  # obj همان آبجکت ServiceGroup یا Service است که در حال ویرایش آن هستیم
            if isinstance(obj, ServiceGroup):
                # ۱. مقداردهی اولیه ردیف‌های جدید
                formset.form.base_fields['service_group'].initial = obj.id
                # ۲. مخفی کردن فیلد 'service' (چون این ساعت کاری مربوط به گروه است)
                formset.form.base_fields['service'].widget = forms.HiddenInput()
            elif isinstance(obj, Service):
                # ۱. مقداردهی اولیه ردیف‌های جدید
                formset.form.base_fields['service'].initial = obj.id
                # ۲. مخفی کردن فیلد 'service_group'
                formset.form.base_fields['service_group'].widget = forms.HiddenInput()
        return formset


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class ServiceInline(admin.TabularInline):
    """
    نمایش فرم‌های "خدمت" (زیرگروه) به صورت ردیفی (Inline)
    در داخل صفحه "گروه خدماتی".
    """
    model = Service
    extra = 1
    verbose_name = "خدمت"
    verbose_name_plural = "خدمات (زیرگروه‌ها)"

@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'home_page_image', 'allow_multiple_selection', 'has_devices')
    search_fields = ('name',)
    # افزودن اینلاین‌های خدمات و ساعات کاری به این صفحه
    inlines = [ServiceInline, WorkHoursInline]
    # استفاده از رابط کاربری بهتر برای فیلد ManyToMany
    filter_horizontal = ('available_devices',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'duration', 'price')
    search_fields = ('name', 'group__name')
    list_filter = ('group',)
    # افزودن اینلاین ساعات کاری (اختصاصی) به این صفحه
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
    raw_id_fields = ('service',)  # جستجوی خدمت به جای دراپ‌داون

@admin.register(DiscountCode)
class DiscountCodeAdmin(ModelAdminJaliMixin, admin.ModelAdmin):
    """
    استفاده از ModelAdminJaliMixin برای نمایش تقویم شمسی
    در فیلدهای تاریخ شروع و انقضا.
    """
    list_display = ('code', 'discount_type', 'value', 'start_date', 'end_date', 'is_active', 'user', 'is_one_time', 'is_used')
    list_filter = ('is_active', 'discount_type', 'is_one_time', 'is_used', 'user')
    search_fields = ('code', 'user__username')
    raw_id_fields = ('user',)  # جستجوی کاربر به جای دراپ‌داون