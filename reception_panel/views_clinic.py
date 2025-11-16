# reception_panel/views_clinic.py
"""
این فایل شامل تمام ویوهای مربوط به مدیریت تنظیمات کلینیک،
شامل خدمات (Services) و ساعات کاری (WorkHours) است.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .forms import ReceptionServiceUpdateForm, WorkHoursFormSet
from .decorators import staff_required
from clinic.models import Service, ServiceGroup, WorkHours


@staff_required
def service_list_view(request):
    """
    صفحه اصلی مدیریت خدمات.
    لیست گروه‌های خدماتی و خدمات زیرمجموعه آن‌ها را نمایش می‌دهد.
    """
    service_groups = ServiceGroup.objects.prefetch_related('services').all()
    context = {
        'service_groups': service_groups
    }
    return render(request, 'reception_panel/service_list.html', context)

@staff_required
def service_update_view(request, pk):
    """
    ویو برای ویرایش جزئیات یک "خدمت" (Service).
    (فقط فیلدهای مجاز در ReceptionServiceUpdateForm مانند نام و مدت زمان)
    """
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ReceptionServiceUpdateForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f"خدمت '{service.name}' با موفقیت به‌روزرسانی شد.")
            return redirect('reception_panel:service_list')
    else:
        form = ReceptionServiceUpdateForm(instance=service)
    
    context = {
        'form': form,
        'service': service
    }
    return render(request, 'reception_panel/service_form.html', context)

@staff_required
def work_hours_update_view(request, group_id=None, service_id=None):
    """
    یک ویو قدرتمند برای مدیریت ساعات کاری با استفاده از FormSet.
    این ویو دو حالت دارد:
    1. اگر group_id ارسال شود: ساعات کاری "گروه" را ویرایش می‌کند.
    2. اگر service_id ارسال شود: ساعات کاری اختصاصی "خدمت" را ویرایش می‌کند.
    """
    parent_obj = None
    queryset = WorkHours.objects.none()
    form_title = ""

    if group_id:
        # حالت ۱: ویرایش ساعات گروه
        parent_obj = get_object_or_404(ServiceGroup, pk=group_id)
        queryset = WorkHours.objects.filter(service_group=parent_obj).order_by('day_of_week', 'start_time')
        form_title = f"ویرایش ساعات کاری گروه: {parent_obj.name}"
    elif service_id:
        # حالت ۲: ویرایش ساعات خدمت
        parent_obj = get_object_or_404(Service, pk=service_id)
        queryset = WorkHours.objects.filter(service=parent_obj).order_by('day_of_week', 'start_time')
        form_title = f"ویرایش ساعات کاری خدمت: {parent_obj.name}"
    else:
        # اگر هیچکدام ارسال نشده بود، بازگرداندن به لیست خدمات
        return redirect('reception_panel:service_list')

    if request.method == 'POST':
        formset = WorkHoursFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            # ابتدا فرم‌های تغییر کرده یا جدید را در حافظه ذخیره می‌کنیم (commit=False)
            instances = formset.save(commit=False) 
            
            for instance in instances:
                # برای ردیف‌های "جدید"، باید والد (گروه یا خدمت) را به صورت دستی تنظیم کنیم
                if group_id:
                    instance.service_group = parent_obj
                    instance.service = None  # اطمینان از عدم تداخل
                elif service_id:
                    instance.service = parent_obj
                    instance.service_group = None  # اطمینان از عدم تداخل
                
                instance.save()  # ذخیره نهایی ردیف در دیتابیس
            
            # مدیریت ردیف‌هایی که برای حذف علامت‌گذاری شده‌اند
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "ساعات کاری با موفقیت به‌روزرسانی شد.")
            return redirect('reception_panel:service_list')
    else:
        # ساخت فرمست در حالت GET
        formset = WorkHoursFormSet(queryset=queryset)

    context = {
        'formset': formset,
        'title': form_title,
    }
    return render(request, 'reception_panel/work_hours_form.html', context)