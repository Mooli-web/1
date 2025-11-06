# a_copy/booking/forms.py

from django import forms
from clinic.models import Testimonial

class RatingForm(forms.ModelForm):
    """
    Form for rating an appointment.
    """
    class Meta:
        model = Testimonial
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, str(i)) for i in range(1, 6)], 
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'rating': 'امتیاز شما (از ۱ تا ۵)',
            'comment': 'نظر شما',
        }