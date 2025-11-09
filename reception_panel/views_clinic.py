# reception_panel/views_clinic.py
# فایل جدید: شامل تمام ویوهای مربوط به مدیریت خدمات و ساعات کاری کلینیک.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .forms import ReceptionServiceUpdateForm, WorkHoursFormSet
from .decorators import staff_required
from clinic.models import Service, ServiceGroup, WorkHours


@staff_required
def service_list_view(request):
    service_groups = ServiceGroup.objects.prefetch_related('services').all()
    context = {
        'service_groups': service_groups
    }
    return render(request, 'reception_panel/service_list.html', context)

@staff_required
def service_update_view(request, pk):
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
    if group_id:
        parent_obj = get_object_or_404(ServiceGroup, pk=group_id)
        queryset = WorkHours.objects.filter(service_group=parent_obj).order_by('day_of_week', 'start_time')
        form_title = f"ویرایش ساعات کاری گروه: {parent_obj.name}"
    elif service_id:
        parent_obj = get_object_or_404(Service, pk=service_id)
        queryset = WorkHours.objects.filter(service=parent_obj).order_by('day_of_week', 'start_time')
        form_title = f"ویرایش ساعات کاری خدمت: {parent_obj.name}"
    else:
        return redirect('reception_panel:service_list')

    if request.method == 'POST':
        formset = WorkHoursFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            # Get new/changed instances, but don't save to DB yet
            instances = formset.save(commit=False) 
            
            for instance in instances:
                # Set the correct foreign key for new forms
                if group_id:
                    instance.service_group = parent_obj
                    instance.service = None # Ensure constraint is met
                elif service_id:
                    instance.service = parent_obj
                    instance.service_group = None # Ensure constraint is met
                
                instance.save() # Commit this instance
            
            # --- MODIFIED: Correctly handle deletions ---
            # Loop through deleted forms and delete objects
            for obj in formset.deleted_objects:
                obj.delete()
            # --- REPLACED: formset.save_m2m() ---

            messages.success(request, "ساعات کاری با موفقیت به‌روزرسانی شد.")
            return redirect('reception_panel:service_list')
    else:
        formset = WorkHoursFormSet(queryset=queryset)

    context = {
        'formset': formset,
        'title': form_title,
    }
    return render(request, 'reception_panel/work_hours_form.html', context)