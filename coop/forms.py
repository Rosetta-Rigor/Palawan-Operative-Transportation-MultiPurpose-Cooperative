from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Member, Vehicle, Batch, Document, DocumentEntry, Announcement

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'profile_image']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class CustomUserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    id_image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    profile_image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = User
        fields = ("username", "full_name", "email", "phone_number", "id_image", "profile_image", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['full_name', 'batch', 'batch_monitoring_number', 'is_dormant', 'user_account']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'batch_monitoring_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_dormant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'user_account': forms.Select(attrs={'class': 'form-control'}),
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'plate_number', 'engine_number', 'chassis_number', 'make_brand',
            'year_model', 'series', 'color', 'member'
            
        ]
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'engine_number': forms.TextInput(attrs={'class': 'form-control'}),
            'chassis_number': forms.TextInput(attrs={'class': 'form-control'}),
            'make_brand': forms.TextInput(attrs={'class': 'form-control'}),
            'year_model': forms.NumberInput(attrs={'class': 'form-control'}),
            'series': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'member': forms.Select(attrs={'class': 'form-control'}),
        }

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['number', 'created_by']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'created_by': forms.Select(attrs={'class': 'form-control'}),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['tin', 'vehicle']
        widgets = {
            'tin': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
        }

class DocumentEntryForm(forms.ModelForm):
    class Meta:
        model = DocumentEntry
        fields = ['document', 'renewal_date', 'official_receipt', 'certificate_of_registration']
        widgets = {
            'document': forms.Select(attrs={'class': 'form-control'}),
            'renewal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'official_receipt': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'certificate_of_registration': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['message', 'recipients']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recipients': forms.SelectMultiple(attrs={'class': 'form-control select2', 'style': 'width:100%'}),
        }
        help_texts = {
            'recipients': 'Select client accounts that should receive this announcement. Leave empty to target all clients.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # limit recipients queryset to client role users
        UserModel = get_user_model()
        self.fields['recipients'].queryset = UserModel.objects.filter(role__iexact='client')
