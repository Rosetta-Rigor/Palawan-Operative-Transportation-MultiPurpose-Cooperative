from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
import secrets
from datetime import timedelta

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
    dormant = models.IntegerField(default=0)  # 0 = Pending, 1 = Not Dormant
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
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    full_name = models.CharField(max_length=255)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="members")
    batch_monitoring_number = models.PositiveIntegerField()
    is_dormant = models.BooleanField(default=False)
    age = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Member's age")
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, null=True, blank=True, help_text="Member's sex")
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
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=(("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")),
        default="pending"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_entries"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_entries"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    manager_notes = models.TextField(null=True, blank=True)
    def __str__(self):
        return f"{self.document.tin} - {self.renewal_date}"
    
class Announcement(models.Model):
    """
    One-way announcement created by admin/manager targeting client users.
    """
    message = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements_created",
        help_text="Admin or manager who created the announcement"
    )
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="announcements_received",
        limit_choices_to={'role': 'client'},
        help_text="Client accounts that will receive/view this announcement"
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"

    def __str__(self):
        return f"Announcement by {self.created_by or 'system'} @ {self.created_at:%Y-%m-%d %H:%M}"

class QRLoginToken(models.Model):
    """
    Stores QR login tokens tied to a Django User.
    Token can be single-use or have an expiry.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="qr_tokens")
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    single_use = models.BooleanField(default=True)

    def __str__(self):
        return f"QRToken({self.user.username}, active={self.is_active})"

    @classmethod
    def create_token_for_user(cls, user, ttl_hours=24, single_use=True):
        token = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(hours=ttl_hours) if ttl_hours else None
        obj = cls.objects.create(user=user, token=token, expires_at=expires, single_use=single_use)
        return obj

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True


class PasswordResetToken(models.Model):
    """
    Stores password reset verification codes sent via email.
    Used for 2FA during password reset process.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    code = models.CharField(max_length=6, db_index=True)  # 6-digit code
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"PasswordReset({self.user.email}, code={self.code}, used={self.is_used})"
    
    @classmethod
    def create_code_for_user(cls, user, ttl_minutes=15):
        """Generate a 6-digit verification code that expires in 15 minutes"""
        import random
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires = timezone.now() + timedelta(minutes=ttl_minutes)
        
        # Deactivate any previous unused codes
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        obj = cls.objects.create(user=user, code=code, expires_at=expires)
        return obj
    
    def is_valid(self):
        """Check if code is still valid"""
        if self.is_used:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
    
    class Meta:
        ordering = ['-created_at']
    
class PaymentYear(models.Model):
    year = models.PositiveIntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.year)


class CarWashCompliance(models.Model):
    """
    Global car wash compliance configuration.
    This is separate from payment types so compliance tracking is universal
    regardless of which payment type (Basic, Premium, etc.) is used.
    """
    year = models.ForeignKey(
        PaymentYear,
        on_delete=models.CASCADE,
        related_name='carwash_compliance'
    )
    monthly_threshold = models.PositiveIntegerField(
        default=4,
        help_text="Required number of car washes per vehicle per month"
    )
    penalty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Penalty for non-compliance (optional)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Staff member who last updated compliance settings"
    )
    
    class Meta:
        unique_together = ['year']
        verbose_name = "Car Wash Compliance Setting"
        verbose_name_plural = "Car Wash Compliance Settings"
    
    def __str__(self):
        return f"{self.year.year} - Threshold: {self.monthly_threshold}/month"


class PaymentType(models.Model):
    TYPE_CHOICES = [
        ('from_members', 'From Members'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    year = models.ForeignKey(PaymentYear, on_delete=models.CASCADE, related_name='payment_types')
    payment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    members = models.ManyToManyField(Member, related_name='payment_types', blank=True)
    
    # Car Wash specific fields
    is_car_wash = models.BooleanField(default=False, help_text="Is this a car wash payment type?")
    car_wash_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Service price for this car wash type (e.g., Basic=100, Premium=150)"
    )

    def __str__(self):
        return f"{self.name} ({self.year.year})"


class PaymentEntry(models.Model):
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE, related_name='entries')
    member = models.ForeignKey('Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_entries')  # Optional now for public customers
    month = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 13)])  # 1=Jan, 12=Dec
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Car Wash specific fields
    is_car_wash_record = models.BooleanField(default=False, help_text="Is this a car wash record entry?")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='carwash_entries', help_text="Specific vehicle for car wash record (optional for public customers)")
    is_penalty = models.BooleanField(default=False, help_text="Is this a penalty payment for non-compliance?")
    
    # Public customer fields
    is_public_customer = models.BooleanField(
        default=False,
        help_text="True if this is a public (non-member) car wash customer"
    )
    customer_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Name of public customer (if not a member)"
    )

    class Meta:
        indexes = [
            models.Index(fields=['is_public_customer']),
        ]

    def __str__(self):
        if self.is_public_customer and self.customer_name:
            return f"{self.payment_type.name} - {self.customer_name} (Public) - Month {self.month}"
        elif self.member:
            return f"{self.payment_type.name} - {self.member.full_name} - Month {self.month}"
        return f"{self.payment_type.name} - Other - Month {self.month}"

    def update_carry_over(self):
        """Update carry-over based on underpayment."""
        self.carry_over = max(0, self.amount_due - self.amount_paid)
        self.save()

# Signals or logic should be added in views/forms to:
# - Sync Member info to User account
# - Only show unassigned vehicles in member add/edit forms
# - Only allow batch creation by admins
# - Handle dormant/activate status
# - Handle document creation and renewal logic
