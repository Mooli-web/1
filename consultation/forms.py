# consultation/forms.py
"""
فرم‌های مورد استفاده در اپلیکیشن consultation.
"""

from django import forms
from .models import ConsultationRequest, ConsultationMessage
# کدهای مربوط به Specialist به طور کامل حذف شدند.

class ConsultationRequestForm(forms.ModelForm):
    """
    فرم ایجاد "درخواست مشاوره" جدید توسط بیمار.
    """
    class Meta:
        model = ConsultationRequest
        # فیلد 'specialist' از اینجا حذف شده است.
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'subject': 'موضوع مشاوره',
            'description': 'شرح درخواست',
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
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'پیام خود را بنویسید...'}),
        }
        labels = {
            'message': 'پیام شما',
        }