# users/allauth_forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class AllauthSignupForm(forms.Form):
    """
    دریافت اطلاعات تکمیلی هنگام ثبت‌نام.
    اصلاح شده: افزودن فیلدهای نام و نام خانوادگی به فرم.
    """
    first_name = forms.CharField(
        label=_("نام"),
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خود را وارد کنید'})
    )
    last_name = forms.CharField(
        label=_("نام خانوادگی"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'})
    )
    phone_number = forms.CharField(
        label=_("شماره تلفن"), 
        max_length=15, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09xxxxxxxxx'})
    )
    gender = forms.ChoiceField(
        label=_("جنسیت"), 
        choices=CustomUser.Gender.choices, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def signup(self, request, user):
        """
        ذخیره اطلاعات تکمیلی روی آبجکت کاربر پس از ثبت‌نام اولیه.
        """
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.gender = self.cleaned_data['gender']
        
        # تعیین نقش پیش‌فرض
        user.role = CustomUser.Role.PATIENT
        
        # ذخیره نهایی کاربر در دیتابیس
        user.save()