# booking/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from clinic.models import Testimonial

class RatingForm(forms.ModelForm):
    """
    فرم ثبت نظر و امتیازدهی توسط بیمار پس از اتمام نوبت.
    """
    class Meta:
        model = Testimonial
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, str(i)) for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'form-control', 
                    'rows': 4,
                    'placeholder': _('تجربه خود را درباره این نوبت بنویسید...')
                }
            ),
        }
        labels = {
            'rating': _('امتیاز شما (از ۱ تا ۵)'),
            'comment': _('نظر شما'),
        }