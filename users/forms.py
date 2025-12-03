# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Profile

class CustomUserCreationForm(UserCreationForm):
    """
    فرم ثبت‌نام ساده شده.
    فقط نام کاربری، موبایل، جنسیت و رمز عبور (که خود جنگو اضافه می‌کند).
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'phone_number', 'gender')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. حذف متن‌های راهنمای پیش‌فرض جنگو
        self.fields['username'].help_text = None
        
        # 2. اجباری کردن جنسیت
        self.fields['gender'].required = True
        
        # 3. تنظیم کلاس‌ها و متن‌های جایگزین (Placeholder)
        # عبارت (انگلیسی) طبق درخواست حذف شد
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'نام کاربری'
        })
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': '09xxxxxxxxx'
        })
        self.fields['gender'].widget.attrs.update({
            'class': 'form-select'
        })

# سایر فرم‌ها بدون تغییر باقی می‌مانند
class UserEditForm(forms.ModelForm):
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
    class Meta:
        model = Profile
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'profile_picture': _('تغییر تصویر پروفایل'),
        }