from django import forms
from .models import Member, Vehicle

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = "__all__"
        widgets = {
            'renewal_date': forms.DateInput(attrs={'type': 'date'}),
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = "__all__"