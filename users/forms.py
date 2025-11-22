# users/forms.py
"""
فرم‌های کاربری (ثبت‌نام و ویرایش).
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Profile

class CustomUserCreationForm(UserCreationForm):
    """
    فرم ثبت‌نام کاربر جدید.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'first_name', 'last_name', 'gender')
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09xxxxxxxxx'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['phone_number'].required = True

class UserEditForm(forms.ModelForm):
    """
    فرم ویرایش اطلاعات پایه کاربر.
    """
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'first_name': _('نام'),
            'last_name': _('نام خانوادگی'),
            'email': _('ایمیل'),
            'gender': _('جنسیت'),
        }

class ProfileEditForm(forms.ModelForm):
    """
    فرم ویرایش پروفایل (فقط عکس).
    """
    class Meta:
        model = Profile
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'profile_picture': _('تغییر تصویر پروفایل'),
        }