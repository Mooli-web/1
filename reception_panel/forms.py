# a_copy/reception_panel/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser, Profile
from django.utils.translation import gettext_lazy as _
# --- ADDED: Imports for new forms ---
from clinic.models import Service, WorkHours
from django.forms import modelformset_factory

class ReceptionLoginForm(forms.Form):
    """
    Login form for staff, similar to DoctorLoginForm.
    """
    username = forms.CharField(label="نام کاربری", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_username'}))
    password = forms.CharField(label="رمز عبور", widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'id_password'}))

class ReceptionPatientCreationForm(UserCreationForm):
    """
    Form for reception to create a new PATIENT.
    We reuse the CustomUserCreationForm but set the role automatically.
    """
    # --- TASK 1: Override username to remove default validators ---
    username = forms.CharField(
        label=_("نام کاربری"),
        max_length=150,
        help_text=_(
            "الزامی. ۱۵۰ کاراکتر یا کمتر. حروف (ف فارسی و انگلیسی)، اعداد و فاصله مجاز است."
        ),
        error_messages={
            "unique": _("کاربری با این نام کاربری از قبل موجود است."),
        },
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # --- TASK 8: Add 'gender' ---
        fields = ('username', 'phone_number', 'first_name', 'last_name', 'email', 'gender')

    # --- ADDED: Make email optional ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['phone_number'].label = 'شماره تلفن'
        self.fields['first_name'].label = 'نام'
        self.fields['last_name'].label = 'نام خانوادگی'
        self.fields['email'].label = 'آدرس ایمیل (اختیاری)'
        # --- TASK 8: Add 'gender' label ---
        self.fields['gender'].label = 'جنسیت'


    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.PATIENT # Automatically set role
        user.is_active = True
        if commit:
            user.save()
        return user

class ReceptionPatientUpdateForm(forms.ModelForm):
    """
    Form for reception to edit a patient's core info.
    """
    class Meta:
        model = CustomUser
        # --- TASK 8: Add 'gender' ---
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'username', 'gender']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'آدرس ایمیل (اختیاری)',
            'phone_number': 'شماره تلفن',
            'username': 'نام کاربری',
            # --- TASK 8: Add 'gender' label ---
            'gender': 'جنسیت',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            # --- TASK 8: Add 'gender' widget ---
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }

    # --- ADDED: Make email optional ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False

class ReceptionProfileUpdateForm(forms.ModelForm):
    """
    Form for reception to edit a patient's profile (points, picture).
    """
    class Meta:
        model = Profile
        fields = ['profile_picture', 'points']
        labels = {
            'profile_picture': 'تصویر پروفایل',
            'points': 'امتیاز کاربر',
        }
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# --- ADDED: Form for editing services (price excluded) ---
class ReceptionServiceUpdateForm(forms.ModelForm):
    class Meta:
        model = Service
        # Price is excluded as requested
        fields = ['name', 'description', 'duration']
        labels = {
            'name': 'نام خدمت',
            'description': 'توضیحات',
            'duration': 'مدت زمان (دقیقه)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# --- ADDED: FormSet for managing WorkHours ---
class WorkHoursForm(forms.ModelForm):
    class Meta:
        model = WorkHours
        # --- MODIFIED: Removed service_group and service ---
        fields = ['day_of_week', 'start_time', 'end_time', 'gender_specific']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'gender_specific': forms.Select(attrs={'class': 'form-select'}),
            # --- MODIFIED: Removed service_group and service widgets ---
        }
        labels = {
            'day_of_week': 'روز هفته',
            'start_time': 'ساعت شروع',
            'end_time': 'ساعت پایان',
            'gender_specific': 'مخصوص جنسیت',
        }

# Create a FormSet factory
WorkHoursFormSet = modelformset_factory(
    WorkHours,
    form=WorkHoursForm,
    extra=1, # Allow adding one new row
    can_delete=True, # Allow deleting rows
    # --- MODIFIED: Removed service_group and service ---
    fields=['day_of_week', 'start_time', 'end_time', 'gender_specific']
)