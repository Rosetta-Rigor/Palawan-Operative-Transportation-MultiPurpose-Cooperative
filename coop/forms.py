from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Member, Vehicle, Batch, Document, DocumentEntry, Announcement, PaymentType, PaymentEntry, PaymentYear, CarWashCompliance

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
        fields = ['full_name', 'batch', 'batch_monitoring_number', 'is_dormant', 'age', 'sex', 'phone_number', 'email', 'user_account']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'batch_monitoring_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_dormant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '150'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +63 912 345 6789'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g., member@example.com'}),
            'user_account': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'phone_number': 'Direct contact number (overridden by linked user account)',
            'email': 'Direct email address (overridden by linked user account)',
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
            'engine_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '70', 'placeholder': 'e.g., ABC2393249RDUI'}),
            'chassis_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '70', 'placeholder': 'e.g., ABC2393249RDUI'}),
            'make_brand': forms.TextInput(attrs={'class': 'form-control'}),
            'year_model': forms.NumberInput(attrs={'class': 'form-control'}),
            'series': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'member': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'engine_number': 'Alphanumeric engine number (up to 70 characters)',
            'chassis_number': 'Alphanumeric chassis number (up to 70 characters)',
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
        fields = ['mv_file_no', 'vehicle']
        widgets = {
            'mv_file_no': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '70', 'placeholder': 'e.g., MV2024-ABC123'}),
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'mv_file_no': 'MV File No.',
        }
        help_texts = {
            'mv_file_no': 'Motor Vehicle File Number (alphanumeric, up to 70 characters)',
        }

class DocumentEntryForm(forms.ModelForm):
    class Meta:
        model = DocumentEntry
        fields = ['document', 'renewal_date', 'official_receipt', 'certificate_of_registration']
        widgets = {
            'document': forms.Select(attrs={'class': 'form-control'}),
            'renewal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'DD/MM/YYYY'}),
            'official_receipt': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'certificate_of_registration': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'renewal_date': 'Renewal Date (D/M/Y)',
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


# Car Wash Forms
class CarWashComplianceForm(forms.ModelForm):
    """Form for configuring global car wash compliance threshold"""
    class Meta:
        model = CarWashCompliance
        fields = ['monthly_threshold', 'penalty_amount']
        widgets = {
            'monthly_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '4',
                'min': '1',
                'max': '31'
            }),
            'penalty_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            })
        }
        labels = {
            'monthly_threshold': 'Monthly Threshold (washes per vehicle)',
            'penalty_amount': 'Penalty Amount (optional)'
        }
        help_texts = {
            'monthly_threshold': 'Required car washes per vehicle per month (applies to all members)',
            'penalty_amount': 'Penalty for non-compliance (leave as 0 if no penalty)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # All fields required
        self.fields['monthly_threshold'].required = True
        self.fields['penalty_amount'].required = False


class CarWashTypeForm(forms.ModelForm):
    """Form for creating car wash payment types (Basic, Premium, etc.)"""
    class Meta:
        model = PaymentType
        fields = ['name', 'car_wash_amount']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Basic Wash, Premium Wash, Full Detail',
                'maxlength': '100'
            }),
            'car_wash_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            })
        }
        labels = {
            'name': 'Car Wash Service Name',
            'car_wash_amount': 'Service Price'
        }
        help_texts = {
            'name': 'Name of the car wash service (e.g., Basic, Premium, Deluxe)',
            'car_wash_amount': 'Price for this service (members and public customers will pay this amount)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['car_wash_amount'].required = True
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_car_wash = True  # Automatically mark as car wash type
        if commit:
            instance.save()
        return instance


class CarWashRecordForm(forms.ModelForm):
    """Form for logging car wash records (member or public)"""
    
    # NEW FIELD: Customer Type Selection
    customer_type = forms.ChoiceField(
        choices=[
            ('member', 'Cooperative Member'),
            ('public', 'Public Customer')
        ],
        initial='member',
        widget=forms.RadioSelect(attrs={'class': 'customer-type-radio'}),
        label='Customer Type'
    )
    
    # NEW FIELD: Existing public customer selector (populated dynamically)
    existing_customer = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_existing_customer'
        }),
        label='Select Existing Customer',
        help_text='Choose from previously registered public customers or enter a new name below'
    )
    
    class Meta:
        model = PaymentEntry
        fields = [
            'payment_type',     # Multiple car wash types available (Basic, Premium, etc.)
            'member',           # Required for members, hidden for public
            'vehicle',          # Required for members, optional for public
            'customer_name',    # Hidden for members, required for public
            'month'
        ]
        widgets = {
            'payment_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'member': forms.Select(attrs={'class': 'form-control select2'}),
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Or enter a new customer name',
                'id': 'id_customer_name_input'
            }),
            'month': forms.Select(attrs={'class': 'form-control'})
        }
        labels = {
            'payment_type': 'Car Wash Service Type',
            'member': 'Member',
            'vehicle': 'Vehicle',
            'customer_name': 'New Customer Name',
            'customer_name': 'Customer Name',
            'month': 'Month'
        }
        help_texts = {
            'payment_type': 'Select the type of car wash service provided',
            'member': 'Select member (only members with vehicles shown)',
            'vehicle': 'Select the specific vehicle that was washed',
            'customer_name': 'Enter the name of the public customer',
            'month': 'Select the month for this record'
        }
    
    def __init__(self, *args, **kwargs):
        year_id = kwargs.pop('year_id', None)
        super().__init__(*args, **kwargs)
        
        # Filter payment types to only car wash types
        if year_id:
            self.fields['payment_type'].queryset = PaymentType.objects.filter(
                year_id=year_id,
                is_car_wash=True
            ).order_by('name')
        else:
            self.fields['payment_type'].queryset = PaymentType.objects.filter(
                is_car_wash=True
            ).order_by('name')
        
        # Populate existing public customers (distinct names from previous records)
        existing_customers = PaymentEntry.objects.filter(
            is_public_customer=True,
            customer_name__isnull=False
        ).exclude(
            customer_name=''
        ).values_list('customer_name', flat=True).distinct().order_by('customer_name')
        
        customer_choices = [('', '-- Select existing customer or enter new below --')]
        customer_choices.extend([(name, name) for name in existing_customers])
        self.fields['existing_customer'].choices = customer_choices
        
        # Filter members to only those with vehicles
        from .models import Member
        self.fields['member'].queryset = Member.objects.filter(
            vehicles__isnull=False
        ).distinct().order_by('full_name')
        
        # Make member and vehicle not required by default (conditional validation in clean())
        self.fields['member'].required = False
        self.fields['vehicle'].required = False
        self.fields['customer_name'].required = False
        
        # Initial vehicle queryset (will be updated via AJAX based on member selection)
        from .models import Vehicle
        self.fields['vehicle'].queryset = Vehicle.objects.none()
        
        if 'member' in self.data:
            try:
                member_id = int(self.data.get('member'))
                self.fields['vehicle'].queryset = Vehicle.objects.filter(
                    member_id=member_id
                ).order_by('plate_number')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.member:
            self.fields['vehicle'].queryset = self.instance.member.vehicles.order_by('plate_number')
    
    def clean(self):
        cleaned_data = super().clean()
        customer_type = cleaned_data.get('customer_type')
        member = cleaned_data.get('member')
        vehicle = cleaned_data.get('vehicle')
        customer_name = cleaned_data.get('customer_name')
        existing_customer = cleaned_data.get('existing_customer')
        payment_type = cleaned_data.get('payment_type')
        
        # Validate based on customer type
        if customer_type == 'member':
            # For members: require member and vehicle
            if not member:
                self.add_error('member', 'Member is required for member transactions.')
            if not vehicle:
                self.add_error('vehicle', 'Vehicle is required for member transactions.')
            # Set flags
            cleaned_data['is_public_customer'] = False
            cleaned_data['customer_name'] = None  # Clear any public customer name
            
        elif customer_type == 'public':
            # For public customers: use existing customer name or require new one
            final_customer_name = None
            
            if existing_customer:
                # User selected an existing customer
                final_customer_name = existing_customer
            elif customer_name and customer_name.strip():
                # User entered a new customer name
                final_customer_name = customer_name.strip()
            else:
                # Neither selected nor entered
                self.add_error('customer_name', 'Please select an existing customer or enter a new name.')
                self.add_error('existing_customer', 'Please select an existing customer or enter a new name.')
            
            cleaned_data['customer_name'] = final_customer_name
            
            # Set flags
            cleaned_data['is_public_customer'] = True
            cleaned_data['member'] = None  # Clear member
            cleaned_data['vehicle'] = None  # Clear vehicle
            
        else:
            raise forms.ValidationError('Invalid customer type selected.')
        
        # Set car wash specific flags and amount from payment type
        cleaned_data['is_car_wash_record'] = True
        
        # Set amount from payment type (for both members and public customers)
        if payment_type and payment_type.car_wash_amount:
            cleaned_data['amount_paid'] = payment_type.car_wash_amount
        else:
            # Fallback to 0 if no amount is set
            cleaned_data['amount_paid'] = 0
        
        return cleaned_data