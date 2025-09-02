from django import forms
from .models import Member, Vehicle, Document

class MemberForm(forms.ModelForm):
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(member__isnull=True),
        required=False,
        label="Assign Existing Vehicle",
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    class Meta:
        model = Member
        fields = ['name', 'gmail', 'batch', 'file_number', 'renewal_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control select2'}),
            'gmail': forms.EmailInput(attrs={'class': 'form-control select2'}),
            'batch': forms.Select(attrs={'class': 'form-control select2'}),
            'file_number': forms.TextInput(attrs={'class': 'form-control select2'}),
            'renewal_date': forms.DateInput(attrs={'class': 'form-control select2', 'type': 'date'}),
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = "__all__"
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control select2'}),
            'engine_number': forms.TextInput(attrs={'class': 'form-control select2'}),
            'chassis_number': forms.TextInput(attrs={'class': 'form-control select2'}),
            'make_brand': forms.TextInput(attrs={'class': 'form-control select2'}),
            'body_type': forms.TextInput(attrs={'class': 'form-control select2'}),
            'year_model': forms.NumberInput(attrs={'class': 'form-control select2'}),
            'series': forms.TextInput(attrs={'class': 'form-control select2'}),
            'color': forms.TextInput(attrs={'class': 'form-control select2'}),
            'member': forms.Select(attrs={'class': 'form-control select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Member.objects.filter(vehicle__isnull=True)
        if self.instance and self.instance.member:
            qs = Member.objects.filter(vehicle__isnull=True) | Member.objects.filter(pk=self.instance.member.pk)
        self.fields['member'].queryset = qs.distinct()

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['vehicle', 'renewal_date', 'official_receipt', 'certificate_of_registration']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-control select2'}),
            'renewal_date': forms.DateInput(attrs={'class': 'form-control select2', 'type': 'date'}),
            'official_receipt': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'certificate_of_registration': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
