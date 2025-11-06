from django import forms
from .models import ConsultationRequest, ConsultationMessage
# from clinic.models import Specialist # <-- REMOVED

class ConsultationRequestForm(forms.ModelForm):
    # --- REMOVED: Specialist choice field ---
    # specialist = forms.ModelChoiceField(
    #    ...
    # )

    class Meta:
        model = ConsultationRequest
        # --- REMOVED: 'specialist' from fields ---
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

class ConsultationMessageForm(forms.ModelForm):
    class Meta:
        model = ConsultationMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'پیام خود را بنویسید...'}),
        }