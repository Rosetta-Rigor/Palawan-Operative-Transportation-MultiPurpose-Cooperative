from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import UserCreationForm

class CustomUserRegistrationForm(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
        return user
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "phone_number", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
from django import forms
from .models import Member, Vehicle, Document, DocumentEntry, Batch

class MemberForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(member__isnull=True),
        required=False,
        label="Assign Existing Vehicle",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    class Meta:
        model = Member
        fields = [
            'full_name', 'phone_number', 'email', 'batch', 'batch_monitoring_number', 'is_dormant'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control select2'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control select2'}),
            'email': forms.EmailInput(attrs={'class': 'form-control select2'}),
            'batch': forms.Select(attrs={'class': 'form-control select2'}),
            'batch_monitoring_number': forms.NumberInput(attrs={'class': 'form-control select2'}),
            'is_dormant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'plate_number', 'engine_number', 'chassis_number', 'make_brand',
            'year_model', 'series', 'color', 'member'
        ]
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control select2'}),
            'engine_number': forms.TextInput(attrs={'class': 'form-control select2'}),
            'chassis_number': forms.TextInput(attrs={'class': 'form-control select2'}),
            'make_brand': forms.TextInput(attrs={'class': 'form-control select2'}),
            'year_model': forms.NumberInput(attrs={'class': 'form-control select2'}),
            'series': forms.TextInput(attrs={'class': 'form-control select2'}),
            'color': forms.TextInput(attrs={'class': 'form-control select2'}),
            'member': forms.Select(attrs={'class': 'form-control select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Member.objects.filter(vehicles__isnull=True)
        if self.instance and self.instance.member:
            qs = Member.objects.filter(vehicles__isnull=True) | Member.objects.filter(pk=self.instance.member.pk)
        self.fields['member'].queryset = qs.distinct()

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['tin', 'vehicle']
        widgets = {
            'tin': forms.TextInput(attrs={'class': 'form-control select2'}),
            'vehicle': forms.Select(attrs={'class': 'form-control select2'}),
        }

class DocumentEntryForm(forms.ModelForm):
    class Meta:
        model = DocumentEntry
        fields = ['document', 'renewal_date', 'official_receipt', 'certificate_of_registration']
        widgets = {
            'document': forms.Select(attrs={'class': 'form-control select2'}),
            'renewal_date': forms.DateInput(attrs={'class': 'form-control select2', 'type': 'date'}),
            'official_receipt': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'certificate_of_registration': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['number']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control select2'}),
        }
