from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
import secrets
from datetime import timedelta

def document_upload_path(instance, filename, doc_type):
    """
    Store files in: media/<MV_FILE_NO>/<renewal_date>/<doc_type>/<filename>
    """
    mv_file_no = instance.document.mv_file_no if hasattr(instance, 'document') and instance.document else "unknown_mv_file"
    renewal_date = instance.renewal_date.strftime("%Y-%m-%d") if instance.renewal_date else "unknown_date"
    return f"{mv_file_no}/{renewal_date}/{doc_type}/{filename}"

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
    phone_number = models.CharField(max_length=20, null=True, blank=True, help_text="Member's phone number (overridden by user account if linked)")
    email = models.EmailField(null=True, blank=True, help_text="Member's email (overridden by user account if linked)")
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
    engine_number = models.CharField(max_length=70, blank=True, null=True, help_text="Engine number (alphanumeric, e.g., ABC2393249RDUI)")
    chassis_number = models.CharField(max_length=70, blank=True, null=True, help_text="Chassis number (alphanumeric, e.g., ABC2393249RDUI)")
    make_brand = models.CharField(max_length=100, blank=True, null=True)
    body_type = models.CharField(max_length=50, default="van", editable=False)
    year_model = models.PositiveIntegerField(blank=True, null=True)
    series = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicles")
    def __str__(self):
        return self.plate_number

class Document(models.Model):
    mv_file_no = models.CharField(max_length=70, unique=True, null=True, blank=True, help_text="MV File Number (alphanumeric, varies per vehicle)")
    vehicle = models.OneToOneField(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="document")
    def __str__(self):
        return f"MV File #{self.mv_file_no}" if self.mv_file_no else f"Document #{self.pk}"

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
        return f"{self.document.mv_file_no} - {self.renewal_date}"
    
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
    
    # From Members specific field
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Monthly amount for 'From Members' payment types (e.g., 200.00)"
    )
    
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
    
    def yearly_total(self):
        """Calculate yearly total for from_members types"""
        if self.payment_type == 'from_members' and self.amount:
            return self.amount * 12
        return None
    
    def member_balance(self, member):
        """Calculate remaining balance for a member"""
        from django.db.models import Sum
        if self.payment_type != 'from_members' or not self.amount:
            return None
        
        yearly_total = self.yearly_total()
        paid_amount = self.entries.filter(member=member).aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        
        return max(yearly_total - paid_amount, 0)


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


class Notification(models.Model):
    """
    Universal notification model for both admin and user notifications
    """
    
    # Recipient
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who receives this notification"
    )
    
    # Notification Content
    title = models.CharField(
        max_length=200,
        help_text="Short notification title"
    )
    message = models.TextField(
        help_text="Detailed notification message"
    )
    
    # Categorization
    CATEGORY_CHOICES = [
        # Admin/Manager Categories
        ('user_registration', 'New User Registration'),
        ('document_uploaded', 'Document Uploaded'),
        ('renewal_urgent', 'Urgent Renewal'),
        ('renewal_upcoming', 'Upcoming Renewal'),
        ('payment_missing', 'Payment Missing'),
        ('carwash_noncompliance', 'Car Wash Non-Compliance'),
        ('batch_deadline', 'Batch Deadline'),
        ('system_alert', 'System Alert'),
        
        # User/Member Categories
        ('account_activated', 'Account Activated'),
        ('document_approved', 'Document Approved'),
        ('document_rejected', 'Document Rejected'),
        ('renewal_reminder', 'Renewal Reminder'),
        ('renewal_due_soon', 'Renewal Due Soon'),
        ('payment_recorded', 'Payment Recorded'),
        ('carwash_reminder', 'Car Wash Reminder'),
        ('announcement_posted', 'New Announcement'),
        ('account_warning', 'Account Warning'),
        ('welcome_message', 'Welcome Message'),
    ]
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        db_index=True
    )
    
    # Priority
    PRIORITY_CHOICES = [
        ('urgent', 'Urgent'),      # Red - Immediate action required
        ('high', 'High'),          # Orange - Important, action soon
        ('normal', 'Normal'),      # Blue - Standard notification
        ('low', 'Low'),            # Gray - Informational only
    ]
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        db_index=True
    )
    
    # Action Link (optional)
    action_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL to redirect user when notification is clicked"
    )
    action_text = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Text for action button (e.g., 'View Document', 'Approve Now')"
    )
    
    # Related Objects (generic foreign keys for flexibility)
    related_object_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Type of related object (e.g., 'member', 'vehicle', 'document')"
    )
    related_object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="ID of related object"
    )
    
    # Status
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether notification has been read"
    )
    read_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when notification was read"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_created',
        help_text="Admin/system that triggered this notification"
    )
    
    # Expiry
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Optional expiry date for time-sensitive notifications"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['category', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


# ============================================================================
# LOGGING SYSTEM MODELS
# ============================================================================

class PaymentLog(models.Model):
    """
    Comprehensive logging for all payment transactions.
    Tracks both member payments (dues, contributions) and other payments (rentals, services).
    """
    PAYMENT_CATEGORY_CHOICES = [
        ('from_members', 'From Members'),
        ('other', 'Other Payments'),
    ]
    
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('reversed', 'Reversed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('other', 'Other'),
    ]
    
    # Transaction Identification
    transaction_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique transaction ID (e.g., PMT-2025-00123)"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the transaction was logged"
    )
    
    # Category & User
    category = models.CharField(
        max_length=20,
        choices=PAYMENT_CATEGORY_CHOICES,
        db_index=True,
        help_text="Payment category"
    )
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment_logs_created',
        help_text="Staff/admin who logged the payment"
    )
    
    # Member Information (for from_members category)
    member = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_logs',
        help_text="Member who made the payment (if applicable)"
    )
    
    # Other Payment Information (for other category)
    payee_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of person/entity making payment (for non-member payments)"
    )
    
    # Payment Details
    payment_type = models.ForeignKey(
        PaymentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_logs',
        help_text="Type of payment (links to PaymentType)"
    )
    payment_type_name = models.CharField(
        max_length=100,
        help_text="Name of payment type (stored for historical record)"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount in PHP"
    )
    payment_year = models.PositiveIntegerField(
        db_index=True,
        help_text="Year the payment is for"
    )
    payment_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 13)],
        help_text="Month the payment is for (if applicable)"
    )
    
    # Payment Method & Receipt
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        help_text="Method of payment"
    )
    receipt_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Official receipt number"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bank reference or transaction reference"
    )
    
    # Status & Notes
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='confirmed',
        db_index=True,
        help_text="Transaction status"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional comments or remarks"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description (mainly for other payments)"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Payment Log"
        verbose_name_plural = "Payment Logs"
        indexes = [
            models.Index(fields=['-timestamp', 'category']),
            models.Index(fields=['payment_year', 'payment_month']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.get_display_name()} - ₱{self.amount}"
    
    def get_display_name(self):
        """Return member name or payee name"""
        if self.member:
            return self.member.full_name
        return self.payee_name or "Unknown"
    
    @classmethod
    def generate_transaction_id(cls, category):
        """Generate unique transaction ID"""
        from django.utils import timezone
        year = timezone.now().year
        prefix = 'PMT' if category == 'from_members' else 'OTH'
        
        # Get last transaction for this year and category
        last_log = cls.objects.filter(
            transaction_id__startswith=f"{prefix}-{year}-"
        ).order_by('-transaction_id').first()
        
        if last_log:
            # Extract number and increment
            try:
                last_num = int(last_log.transaction_id.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}-{year}-{new_num:05d}"


class CarWashLog(models.Model):
    """
    Comprehensive logging for all car wash transactions.
    Tracks both member services (compliance) and public customer services.
    """
    CUSTOMER_TYPE_CHOICES = [
        ('member', 'Member'),
        ('public', 'Public Customer'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Transaction Identification
    transaction_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique transaction ID (e.g., CW-2025-00234)"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the service was logged"
    )
    
    # Staff & Customer
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='carwash_logs_created',
        help_text="Staff/admin who logged the service"
    )
    customer_type = models.CharField(
        max_length=10,
        choices=CUSTOMER_TYPE_CHOICES,
        db_index=True,
        help_text="Type of customer"
    )
    
    # Member Information (for member services)
    member = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carwash_logs',
        help_text="Member who received service (if applicable)"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carwash_logs',
        help_text="Vehicle that was serviced"
    )
    
    # Public Customer Information
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of public customer (if not a member)"
    )
    vehicle_plate = models.CharField(
        max_length=20,
        blank=True,
        help_text="Plate number for public customer vehicle"
    )
    
    # Service Details
    service_type = models.ForeignKey(
        PaymentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carwash_logs',
        help_text="Type of car wash service (links to PaymentType)"
    )
    service_type_name = models.CharField(
        max_length=100,
        help_text="Name of service type (stored for historical record)"
    )
    service_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Service fee (₱0 for member compliance services)"
    )
    carwash_year = models.PositiveIntegerField(
        db_index=True,
        help_text="Year the service is recorded for"
    )
    carwash_month = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 13)],
        db_index=True,
        help_text="Month the service is recorded for"
    )
    
    # Compliance (for members)
    is_compliance = models.BooleanField(
        default=False,
        help_text="Whether this service counts toward member compliance"
    )
    compliance_status = models.CharField(
        max_length=50,
        blank=True,
        help_text="Compliance status text (e.g., 'Compliant (1/4 required)')"
    )
    
    # Status & Notes
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        db_index=True,
        help_text="Service status"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional comments or remarks"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Car Wash Log"
        verbose_name_plural = "Car Wash Logs"
        indexes = [
            models.Index(fields=['-timestamp', 'customer_type']),
            models.Index(fields=['carwash_year', 'carwash_month']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.get_display_name()} - {self.service_type_name}"
    
    def get_display_name(self):
        """Return member name or customer name"""
        if self.member:
            return self.member.full_name
        return self.customer_name or "Walk-in Customer"
    
    @classmethod
    def generate_transaction_id(cls):
        """Generate unique transaction ID"""
        from django.utils import timezone
        year = timezone.now().year
        prefix = 'CW'
        
        # Get last transaction for this year
        last_log = cls.objects.filter(
            transaction_id__startswith=f"{prefix}-{year}-"
        ).order_by('-transaction_id').first()
        
        if last_log:
            # Extract number and increment
            try:
                last_num = int(last_log.transaction_id.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}-{year}-{new_num:05d}"


class LogEmailHistory(models.Model):
    """
    Audit trail for all log emails sent to members.
    Tracks when staff sent transaction history to members via email.
    """
    LOG_TYPE_CHOICES = [
        ('payment', 'Payment Logs'),
        ('carwash', 'Car Wash Logs'),
        ('combined', 'Combined Logs'),
    ]
    
    # Email Details
    sent_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the email was sent"
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='log_emails_sent',
        help_text="Staff member who sent the email"
    )
    recipient_member = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        related_name='log_emails_received',
        help_text="Member who received the email"
    )
    recipient_email = models.EmailField(
        help_text="Email address where logs were sent"
    )
    
    # Log Content
    log_type = models.CharField(
        max_length=20,
        choices=LOG_TYPE_CHOICES,
        help_text="Type of logs included in email"
    )
    date_range_start = models.DateField(
        null=True,
        blank=True,
        help_text="Start date of log range (if filtered)"
    )
    date_range_end = models.DateField(
        null=True,
        blank=True,
        help_text="End date of log range (if filtered)"
    )
    total_records = models.PositiveIntegerField(
        default=0,
        help_text="Number of log records included"
    )
    
    # PDF Attachment
    pdf_generated = models.BooleanField(
        default=False,
        help_text="Whether a PDF was attached"
    )
    
    # Delivery Status
    delivery_status = models.CharField(
        max_length=20,
        choices=[
            ('sent', 'Sent Successfully'),
            ('failed', 'Failed'),
        ],
        default='sent',
        help_text="Email delivery status"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error details if delivery failed"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes from staff"
    )
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Log Email History"
        verbose_name_plural = "Log Email History"
        indexes = [
            models.Index(fields=['-sent_at', 'log_type']),
        ]
    
    def __str__(self):
        member_name = self.recipient_member.full_name if self.recipient_member else "Unknown"
        return f"{self.get_log_type_display()} sent to {member_name} on {self.sent_at.strftime('%Y-%m-%d %H:%M')}"


# Signals or logic should be added in views/forms to:
# - Sync Member info to User account
# - Only show unassigned vehicles in member add/edit forms
# - Only allow batch creation by admins
# - Handle dormant/activate status
# - Handle document creation and renewal logic
