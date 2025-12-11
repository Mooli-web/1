# users/allauth_forms.py
import re
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Profile

class AllauthSignupForm(forms.Form):
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
    referral_code = forms.CharField(
        label=_("کد معرف (اختیاری)"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد دوستتان را وارد کنید'})
    )

    # -----------------------------------------------------------
    # اعتبارسنجی‌ها (Validation)
    # -----------------------------------------------------------

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            # فقط حروف فارسی، انگلیسی و فاصله مجاز است
            if not re.match(r'^[\u0600-\u06FFa-zA-Z\s]+$', first_name):
                raise forms.ValidationError(_("نام باید فقط شامل حروف باشد."))
            if len(first_name) < 2:
                raise forms.ValidationError(_("نام باید حداقل ۲ حرف باشد."))
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            # فقط حروف فارسی، انگلیسی و فاصله مجاز است
            if not re.match(r'^[\u0600-\u06FFa-zA-Z\s]+$', last_name):
                raise forms.ValidationError(_("نام خانوادگی باید فقط شامل حروف باشد."))
            if len(last_name) < 2:
                raise forms.ValidationError(_("نام خانوادگی باید حداقل ۲ حرف باشد."))
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # تبدیل اعداد فارسی به انگلیسی
            transtab = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
            phone_number = phone_number.translate(transtab)

            # بررسی فرمت (۱۱ رقم و شروع با 09)
            if not re.match(r'^09\d{9}$', phone_number):
                raise forms.ValidationError(_("شماره تلفن نامعتبر است. فرمت صحیح: 09123456789"))

            # بررسی تکراری بودن
            if CustomUser.objects.filter(phone_number=phone_number).exists():
                raise forms.ValidationError(_("این شماره تلفن قبلاً در سیستم ثبت شده است."))
        
        return phone_number

    def clean_referral_code(self):
        code = self.cleaned_data.get('referral_code')
        if code:
            # اگر کدی وارد شده، باید معتبر باشد
            if not Profile.objects.filter(referral_code__iexact=code).exists():
                raise forms.ValidationError(_("کد معرف وارد شده نامعتبر است."))
        return code

    # -----------------------------------------------------------
    # ذخیره‌سازی (Save)
    # -----------------------------------------------------------

    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # استفاده از شماره تلفن تمیز شده (انگلیسی شده)
        user.phone_number = self.cleaned_data['phone_number'] 
        user.gender = self.cleaned_data['gender']
        
        user.role = CustomUser.Role.PATIENT
        user.save()

        ref_code = self.cleaned_data.get('referral_code')
        if ref_code:
            # چون در clean_referral_code چک کردیم، اینجا مطمئنیم پروفایل وجود دارد
            try:
                referrer_profile = Profile.objects.get(referral_code__iexact=ref_code)
                user.profile.referred_by = referrer_profile.user
                user.profile.save()
            except Profile.DoesNotExist:
                pass