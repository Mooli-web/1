# consultation/forms.py
"""
فرم‌های مورد استفاده در اپلیکیشن consultation.
"""

from django import forms
from .models import ConsultationRequest, ConsultationMessage

class ConsultationRequestForm(forms.ModelForm):
    """
    فرم ایجاد "درخواست مشاوره" جدید توسط بیمار.
    تغییر: فیلد 'subject' حذف شد تا کاربر درگیر عنوان‌نویسی نشود.
    """
    class Meta:
        model = ConsultationRequest
        # فیلد subject را حذف کردیم، در ویو به صورت خودکار پر می‌شود.
        fields = ['description'] 
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': 'لطفاً سوال یا مشکل خود را اینجا بنویسید...'
            }),
        }
        labels = {
            'description': 'متن پیام شما',
        }

class ConsultationMessageForm(forms.ModelForm):
    """
    فرم ارسال "پیام" جدید در یک مشاوره موجود.
    این فرم هم توسط بیمار و هم توسط پذیرش استفاده می‌شود.
    """
    class Meta:
        model = ConsultationMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'پیام خود را بنویسید...',
                'style': 'resize: none;' # جلوگیری از تغییر سایز زشت
            }),
        }
        labels = {
            'message': '', # لیبل را حذف کردیم تا شبیه مسنجر شود
        }