# booking/forms.py
"""
فرم‌های مورد استفاده در اپلیکیشن booking.
"""

from django import forms
from clinic.models import Testimonial  # مدل "نظر مشتری" از اپ clinic

class RatingForm(forms.ModelForm):
    """
    فرم ثبت نظر (امتیازدهی) توسط بیمار.
    بیمار پس از "انجام شدن" نوبت، می‌تواند با این فرم
    یک آبجکت Testimonial ایجاد کند.
    """
    class Meta:
        model = Testimonial
        # فیلدهایی که بیمار باید پر کند:
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, str(i)) for i in range(1, 6)],  # انتخاب امتیاز از ۱ تا ۵
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'rating': 'امتیاز شما (از ۱ تا ۵)',
            'comment': 'نظر شما',
        }