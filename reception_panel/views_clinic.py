# reception_panel/views_clinic.py
"""
مدیریت تنظیمات کلینیک (خدمات و ساعات کاری).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse

from .forms import ReceptionServiceUpdateForm, WorkHoursFormSet
from .decorators import staff_required
from clinic.models import Service, ServiceGroup, WorkHours

@staff_required
def service_list_view(request: HttpRequest) -> HttpResponse:
    """لیست خدمات."""
    service_groups = ServiceGroup.objects.prefetch_related('services').all()
    return render(request, 'reception_panel/service_list.html', {'service_groups': service_groups})

@staff_required
def service_update_view(request: HttpRequest, pk: int) -> HttpResponse:
    """ویرایش خدمت."""
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ReceptionServiceUpdateForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "خدمت به‌روزرسانی شد.")
            return redirect('reception_panel:service_list')
    else:
        form = ReceptionServiceUpdateForm(instance=service)
    
    return render(request, 'reception_panel/service_form.html', {'form': form, 'service': service})

@staff_required
def work_hours_update_view(request: HttpRequest, group_id: int = None, service_id: int = None) -> HttpResponse:
    """مدیریت ساعات کاری با FormSet."""
    parent_obj = None
    queryset = WorkHours.objects.none()
    title = ""

    if group_id:
        parent_obj = get_object_or_404(ServiceGroup, pk=group_id)
        queryset = WorkHours.objects.filter(service_group=parent_obj)
        title = f"ساعات کاری گروه: {parent_obj.name}"
    elif service_id:
        parent_obj = get_object_or_404(Service, pk=service_id)
        queryset = WorkHours.objects.filter(service=parent_obj)
        title = f"ساعات کاری خدمت: {parent_obj.name}"
    else:
        return redirect('reception_panel:service_list')

    if request.method == 'POST':
        formset = WorkHoursFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            with transaction.atomic():
                instances = formset.save(commit=False)
                for instance in instances:
                    if group_id:
                        instance.service_group = parent_obj
                        instance.service = None
                    elif service_id:
                        instance.service = parent_obj
                        instance.service_group = None
                    instance.save()
                
                for obj in formset.deleted_objects:
                    obj.delete()

            messages.success(request, "ساعات کاری ذخیره شد.")
            return redirect('reception_panel:service_list')
    else:
        formset = WorkHoursFormSet(queryset=queryset)

    return render(request, 'reception_panel/work_hours_form.html', {'formset': formset, 'title': title})