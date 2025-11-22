# reception_panel/forms.py
"""
فرم‌های مورد استفاده در پنل پذیرش.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.forms import modelformset_factory

from users.models import CustomUser, Profile
from clinic.models import Service, WorkHours

class ReceptionLoginForm(forms.Form):
    username = forms.CharField(
        label=_("نام کاربری"), 
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_username'})
    )
    password = forms.CharField(
        label=_("رمز عبور"), 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'id_password'})
    )

class ReceptionPatientCreationForm(UserCreationForm):
    """فرم ایجاد بیمار جدید."""
    username = forms.CharField(
        label=_("نام کاربری"),
        max_length=150,
        help_text=_("الزامی. حروف، اعداد و کاراکترهای مجاز."),
        error_messages={"unique": _("این نام کاربری قبلاً ثبت شده است.")},
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'phone_number', 'first_name', 'last_name', 'email', 'gender')
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'phone_number': _('شماره تلفن'),
            'first_name': _('نام'),
            'last_name': _('نام خانوادگی'),
            'email': _('ایمیل (اختیاری)'),
            'gender': _('جنسیت'),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.PATIENT
        user.is_active = True
        if commit:
            user.save()
        return user

class ReceptionPatientUpdateForm(forms.ModelForm):
    """فرم ویرایش اطلاعات بیمار."""
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'username', 'gender']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'first_name': _('نام'),
            'last_name': _('نام خانوادگی'),
            'email': _('ایمیل'),
            'phone_number': _('شماره تلفن'),
            'username': _('نام کاربری'),
            'gender': _('جنسیت'),
        }

class ReceptionProfileUpdateForm(forms.ModelForm):
    """فرم ویرایش پروفایل و امتیاز بیمار."""
    class Meta:
        model = Profile
        fields = ['profile_picture', 'points']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'profile_picture': _('تصویر پروفایل'),
            'points': _('امتیاز کاربر'),
        }

class ReceptionServiceUpdateForm(forms.ModelForm):
    """فرم ویرایش خدمات."""
    class Meta:
        model = Service
        fields = ['name', 'description', 'duration', 'old_price', 'badge']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'old_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'badge': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': _('نام خدمت'),
            'description': _('توضیحات'),
            'duration': _('مدت زمان (دقیقه)'),
            'old_price': _('قیمت خط‌خورده (تومان)'),
            'badge': _('برچسب بازاریابی'),
        }

class WorkHoursForm(forms.ModelForm):
    """فرم یک ردیف ساعت کاری."""
    class Meta:
        model = WorkHours
        fields = ['day_of_week', 'start_time', 'end_time', 'gender_specific']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'gender_specific': forms.Select(attrs={'class': 'form-select'}),
        }

WorkHoursFormSet = modelformset_factory(
    WorkHours,
    form=WorkHoursForm,
    extra=1,
    can_delete=True
)