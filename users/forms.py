# a_copy/users/forms.py

from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile
from django import forms # <-- ADDED
from django.utils.translation import gettext_lazy as _

class CustomUserCreationForm(UserCreationForm):
    
    # --- TASK 1: Override username to remove default validators ---
    username = forms.CharField(
        label=_("Username"),
        max_length=150,
        help_text=_(
            "الزامی. ۱۵۰ کاراکتر یا کمتر. حروف (فارسی و انگلیسی)، اعداد و فاصله مجاز است."
        ),
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # --- TASK 8: Add 'gender' ---
        fields = ('username', 'email', 'phone_number', 'first_name', 'last_name', 'gender')

    # --- ADDED: Make email optional ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False

# --- ADDED: Form for editing user basic info ---
class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # --- TASK 8: Add 'gender' ---
        fields = ['first_name', 'last_name', 'email', 'gender']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'آدرس ایمیل',
            'gender': 'جنسیت',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            # --- TASK 8: Add 'gender' widget ---
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }

    # --- ADDED: Make email optional ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False

# --- ADDED: Form for editing profile picture ---
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']
        labels = {
            'profile_picture': 'تصویر پروفایل جدید',
        }
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }