# users/allauth_forms.py
"""
فرم سفارشی برای ثبت‌نام در Allauth.
این فرم به عنوان یک افزونه (Mixin) به فرم اصلی Allauth اضافه می‌شود.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class AllauthSignupForm(forms.Form): # تغییر ارث‌بری به فرم ساده جنگو
    """
    دریافت اطلاعات تکمیلی هنگام ثبت‌نام.
    """
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
        این متد توسط Allauth پس از ساخت اولیه کاربر فراخوانی می‌شود.
        در اینجا اطلاعات تکمیلی را روی آبجکت کاربر ذخیره می‌کنیم.
        """
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.gender = self.cleaned_data['gender']
        
        # تعیین نقش پیش‌فرض
        user.role = CustomUser.Role.PATIENT
        
        # ذخیره نهایی کاربر در دیتابیس
        user.save()