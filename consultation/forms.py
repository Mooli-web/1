# consultation/forms.py
"""
فرم‌های اپلیکیشن consultation.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ConsultationRequest, ConsultationMessage

class ConsultationRequestForm(forms.ModelForm):
    """
    فرم ایجاد درخواست مشاوره جدید.
    """
    class Meta:
        model = ConsultationRequest
        fields = ['description'] 
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': _('لطفاً سوال یا مشکل خود را اینجا بنویسید...')
            }),
        }
        labels = {
            'description': _('متن پیام شما'),
        }

class ConsultationMessageForm(forms.ModelForm):
    """
    فرم ارسال پیام جدید در چت.
    """
    class Meta:
        model = ConsultationMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': _('پیام خود را بنویسید...'),
                'style': 'resize: none;'
            }),
        }
        labels = {
            'message': '',
        }