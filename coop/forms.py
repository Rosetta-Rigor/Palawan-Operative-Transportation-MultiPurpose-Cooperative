from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Member, Vehicle, Batch, Document, DocumentEntry, Announcement, PaymentType, PaymentEntry, PaymentYear

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    # Add age and sex fields that will be saved to the linked Member profile
    age = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '150'}),
        help_text="Your age"
    )
    sex = forms.ChoiceField(
        required=False,
        choices=[('', 'Select...')] + [('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Your sex"
    )
    
    class Meta:
        model = User
        # allow editing username, email, phone number and profile picture
        fields = ['username', 'full_name', 'email', 'phone_number', 'profile_image']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate age and sex from member_profile if it exists
        if self.instance and hasattr(self.instance, 'member_profile') and self.instance.member_profile:
            self.fields['age'].initial = self.instance.member_profile.age
            self.fields['sex'].initial = self.instance.member_profile.sex
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        # Save age and sex to linked member_profile if it exists
        if hasattr(user, 'member_profile') and user.member_profile:
            user.member_profile.age = self.cleaned_data.get('age')
            user.member_profile.sex = self.cleaned_data.get('sex')
            if commit:
                user.member_profile.save()
        return user

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'profile_image']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
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
        fields = ['full_name', 'batch', 'batch_monitoring_number', 'is_dormant', 'age', 'sex', 'user_account']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'batch_monitoring_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_dormant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '150'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
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

       
from .models import PaymentYear, PaymentType, PaymentEntry

class PaymentYearForm(forms.ModelForm):
    class Meta:
        model = PaymentYear
        fields = ['year']
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter year (e.g., 2025)'}),
        }
        labels = {
            'year': 'Year',
        }


class PaymentTypeForm(forms.ModelForm):
    class Meta:
        model = PaymentType
        fields = ['name', 'payment_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter payment type name'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Payment Type Name',
            'payment_type': 'Type of Payment',
        }


class PaymentEntryForm(forms.ModelForm):
    class Meta:
        model = PaymentEntry
        fields = ['payment_type', 'member', 'month', 'amount_paid']  # Ensure 'member' is included
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'member': forms.Select(attrs={'class': 'form-control'}),
            'month': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
        }


# Password Reset Forms
class PasswordResetRequestForm(forms.Form):
    """Step 1: User enters email to request password reset"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autofocus': True
        }),
        label='Email Address'
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("This email address is not registered in our system.")
        return email


class PasswordResetVerifyForm(forms.Form):
    """Step 2: User enters 6-digit verification code sent to email"""
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'autofocus': True,
            'style': 'letter-spacing: 8px; text-align: center; font-size: 1.5rem; font-weight: 700;'
        }),
        label='Verification Code'
    )


class PasswordResetConfirmForm(forms.Form):
    """Step 3: User sets new password"""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autofocus': True
        }),
        label='New Password',
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        label='Confirm Password'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data