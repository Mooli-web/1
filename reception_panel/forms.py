# reception_panel/forms.py
"""
این فایل شامل تمام فرم‌های مورد استفاده در "پنل پذیرش" است.
این فرم‌ها به طور خاص برای عملیات‌های پذیرش (مانند ایجاد بیمار
یا ویرایش خدمات) سفارشی‌سازی شده‌اند.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser, Profile
from django.utils.translation import gettext_lazy as _
from clinic.models import Service, WorkHours
from django.forms import modelformset_factory  # برای ساخت فرمست ساعات کاری


class ReceptionLoginForm(forms.Form):
    """
    فرم لاگین ساده برای پنل پذیرش.
    (مشابه فرم لاگین ادمین جنگو اما در صفحه سفارشی)
    """
    username = forms.CharField(label="نام کاربری", widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_username'}))
    password = forms.CharField(label="رمز عبور", widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'id_password'}))

class ReceptionPatientCreationForm(UserCreationForm):
    """
    فرم ایجاد بیمار جدید توسط پذیرش.
    - ارث‌بری از UserCreationForm برای مدیریت استاندارد ایجاد کاربر و رمز عبور.
    - فیلدهای سفارشی مدل CustomUser را شامل می‌شود.
    - به طور خودکار نقش کاربر را "PATIENT" تنظیم می‌کند.
    """
    
    # بازنویسی فیلد username برای سازگاری با CustomUser (اگر نیاز بود)
    username = forms.CharField(
        label=_("نام کاربری"),
        max_length=150,
        help_text=_(
            "الزامی. ۱۵۰ کاراکتر یا کمتر. حروف (فارسی و انگلیسی)، اعداد و فاصله مجاز است."
        ),
        error_messages={
            "unique": _("کاربری با این نام کاربری از قبل موجود است."),
        },
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # فیلدهای مورد نیاز هنگام "ایجاد" بیمار
        fields = ('username', 'phone_number', 'first_name', 'last_name', 'email', 'gender')

    def __init__(self, *args, **kwargs):
        """
        سفارشی‌سازی لیبل‌ها و تنظیمات فیلدها.
        """
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False  # ایمیل در این سیستم اختیاری است
        self.fields['phone_number'].label = 'شماره تلفن'
        self.fields['first_name'].label = 'نام'
        self.fields['last_name'].label = 'نام خانوادگی'
        self.fields['email'].label = 'آدرس ایمیل (اختیاری)'
        self.fields['gender'].label = 'جنسیت'


    def save(self, commit=True):
        """
        بازنویسی متد save برای تنظیم خودکار نقش بیمار.
        """
        user = super().save(commit=False)
        user.role = CustomUser.Role.PATIENT  # --- نکته کلیدی ---
        user.is_active = True  # کاربران ساخته شده توسط پذیرش بلافاصله فعال هستند
        if commit:
            user.save()
        return user

class ReceptionPatientUpdateForm(forms.ModelForm):
    """
    فرم ویرایش اطلاعات "پایه" بیمار (مدل CustomUser) توسط پذیرش.
    """
    class Meta:
        model = CustomUser
        # فیلدهایی که پذیرش مجاز به ویرایش آن‌ها است
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'username', 'gender']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'آدرس ایمیل (اختیاری)',
            'phone_number': 'شماره تلفن',
            'username': 'نام کاربری',
            'gender': 'جنسیت',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False  # ایمیل همچنان اختیاری است

class ReceptionProfileUpdateForm(forms.ModelForm):
    """
    فرم ویرایش اطلاعات "پروفایل" بیمار (مدل Profile) توسط پذیرش.
    پذیرش مجاز به تغییر امتیاز (points) بیمار است.
    """
    class Meta:
        model = Profile
        fields = ['profile_picture', 'points']
        labels = {
            'profile_picture': 'تصویر پروفایل',
            'points': 'امتیاز کاربر',  # --- فیلد حساس ---
        }
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# --- فرم‌های مدیریت کلینیک ---

class ReceptionServiceUpdateForm(forms.ModelForm):
    """
    فرم ویرایش خدمات توسط پذیرش.
    تغییر: فیلدهای badge و old_price اضافه شدند.
    """
    class Meta:
        model = Service
        # پذیرش فقط مجاز به تغییر نام، توضیحات، مدت زمان و فیلدهای بازاریابی است
        fields = ['name', 'description', 'duration', 'old_price', 'badge']
        labels = {
            'name': 'نام خدمت',
            'description': 'توضیحات',
            'duration': 'مدت زمان (دقیقه)',
            'old_price': 'قیمت خط‌خورده (تومان)',
            'badge': 'برچسب بازاریابی',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'old_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'خالی بگذارید اگر تخفیفی ندارد'
            }),
            'badge': forms.Select(attrs={'class': 'form-select'}),
        }

# --- فرم‌ست (FormSet) ساعات کاری ---

class WorkHoursForm(forms.ModelForm):
    """
    فرم پایه برای یک ردیف "ساعت کاری".
    این فرم به تنهایی استفاده نمی‌شود، بلکه به عنوان ورودی به 'modelformset_factory' داده می‌شود.
    """
    class Meta:
        model = WorkHours
        # فیلدهای service_group و service در این فرم نیستند
        # آن‌ها توسط ویو (work_hours_update_view) به صورت دستی مدیریت می‌شوند.
        fields = ['day_of_week', 'start_time', 'end_time', 'gender_specific']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'gender_specific': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'day_of_week': 'روز هفته',
            'start_time': 'ساعت شروع',
            'end_time': 'ساعت پایان',
            'gender_specific': 'مخصوص جنسیت',
        }

# 'WorkHoursFormSet' یک کلاس ساخته شده توسط factory است
WorkHoursFormSet = modelformset_factory(
    WorkHours,
    form=WorkHoursForm,
    extra=1,          # اجازه افزودن 1 ردیف خالی جدید در هر بار
    can_delete=True,  # اجازه تیک زدن چک‌باکس "حذف"
    fields=['day_of_week', 'start_time', 'end_time', 'gender_specific']
)   