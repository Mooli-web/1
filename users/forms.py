# users/forms.py
"""
فرم‌های مربوط به کاربران در بخش عمومی سایت (نه پنل پذیرش).
- فرم ثبت‌نام (SignUp)
- فرم ویرایش اطلاعات پایه توسط خود کاربر (UserEditForm)
- فرم ویرایش پروفایل توسط خود کاربر (ProfileEditForm)
"""

from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile
from django import forms
from django.utils.translation import gettext_lazy as _

class CustomUserCreationForm(UserCreationForm):
    """
    فرم ثبت‌نام عمومی (SignUp) برای کاربران جدید.
    - از UserCreationForm ارث‌بری می‌کند.
    - فیلدهای سفارشی CustomUser را شامل می‌شود.
    """
    
    # بازنویسی فیلد username (مشابه مدل)
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
        # فیلدهایی که کاربر در صفحه ثبت‌نام عمومی وارد می‌کند
        fields = ('username', 'email', 'phone_number', 'first_name', 'last_name', 'gender')

    def __init__(self, *args, **kwargs):
        """
        سفارشی‌سازی فرم. (ایمیل را اختیاری می‌کند)
        """
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False


class UserEditForm(forms.ModelForm):
    """
    فرم ویرایش اطلاعات "پایه" (مدل User) در داشبورد کاربری.
    کاربر با این فرم می‌تواند اطلاعات شخصی خود را ویرایش کند.
    """
    class Meta:
        model = CustomUser
        # کاربر مجاز به ویرایش این فیلدها است
        # (توجه: username و phone_number در این فرم نیستند چون فیلدهای حساس و کلیدی هستند)
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
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        """
        ایمیل در ویرایش نیز اختیاری است.
        """
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False


class ProfileEditForm(forms.ModelForm):
    """
    فرم ویرایش اطلاعات "پروفایل" (مدل Profile) در داشبورد کاربری.
    کاربر با این فرم فقط می‌تواند "تصویر پروفایل" خود را عوض کند.
    (توجه: کاربر مجاز به ویرایش امتیازات خود نیست)
    """
    class Meta:
        model = Profile
        fields = ['profile_picture']  # --- فقط تصویر پروفایل ---
        labels = {
            'profile_picture': 'تصویر پروفایل جدید',
        }
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }