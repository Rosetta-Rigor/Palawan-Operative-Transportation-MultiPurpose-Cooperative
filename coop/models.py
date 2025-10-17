from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone

def document_upload_path(instance, filename, doc_type):
    """
    Store files in: media/<TIN>/<renewal_date>/<doc_type>/<filename>
    """
    tin = instance.document.tin if hasattr(instance, 'document') and instance.document else "unknown_tin"
    renewal_date = instance.renewal_date.strftime("%Y-%m-%d") if instance.renewal_date else "unknown_date"
    return f"{tin}/{renewal_date}/{doc_type}/{filename}"

def or_upload_path(instance, filename):
    return document_upload_path(instance, filename, "or")

def cr_upload_path(instance, filename):
    return document_upload_path(instance, filename, "cr")

def id_upload_path(instance, filename):
    # Store ID images in: media/ID/<username>/<filename>
    return f"ID/{instance.username}/{filename}"

def profile_upload_path(instance, filename):
    return f"profiles/{instance.username}/{filename}"

class User(AbstractUser):
    # Only managers and admins can create accounts
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('client', 'Client Member'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    id_image = models.ImageField(upload_to=id_upload_path, null=True, blank=True)
    profile_image = models.ImageField(upload_to=profile_upload_path, null=True, blank=True)
    email = models.EmailField(unique=True)
    groups = models.ManyToManyField(
        Group,
        related_name="coop_user_set",  # <-- unique related_name
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="coop_user_permissions",  # <-- unique related_name
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions"
    )

class Batch(models.Model):
    number = models.CharField(max_length=20, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'admin'})
    def __str__(self):
        return f"Batch {self.number}"

class Member(models.Model):
    full_name = models.CharField(max_length=255)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="members")
    batch_monitoring_number = models.PositiveIntegerField()
    is_dormant = models.BooleanField(default=False)
    # phone_number and email removed, user_account now on User
    user_account = models.OneToOneField(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='member_profile'
    )
    def __str__(self):
        return self.full_name

class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    engine_number = models.CharField(max_length=50, blank=True, null=True)
    chassis_number = models.CharField(max_length=50, blank=True, null=True)
    make_brand = models.CharField(max_length=100, blank=True, null=True)
    body_type = models.CharField(max_length=50, default="van", editable=False)
    year_model = models.PositiveIntegerField(blank=True, null=True)
    series = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicles")
    def __str__(self):
        return self.plate_number

class Document(models.Model):
    tin = models.CharField(max_length=12, unique=True)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="document")
    def __str__(self):
        return f"TIN {self.tin}"

class DocumentEntry(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="entries")
    renewal_date = models.DateField()
    official_receipt = models.ImageField(upload_to=or_upload_path)
    certificate_of_registration = models.ImageField(upload_to=cr_upload_path)
    def __str__(self):
        return f"{self.document.tin} - {self.renewal_date}"

# Signals or logic should be added in views/forms to:
# - Sync Member info to User account
# - Only show unassigned vehicles in member add/edit forms
# - Only allow batch creation by admins
# - Handle dormant/activate status
# - Handle document creation and renewal logic
