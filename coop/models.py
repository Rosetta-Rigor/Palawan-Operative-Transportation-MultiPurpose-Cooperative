from django.db import models
import datetime

def document_upload_path(instance, filename, doc_type):
    """
    Store files in: media/documents/<member_name>/<renewal_date>/<doc_type>/<filename>
    """
    member_name = instance.vehicle.member.name.replace(" ", "_") if instance.vehicle and instance.vehicle.member else "unknown_member"
    renewal_date = instance.renewal_date
    # Convert renewal_date to date object if it's a string
    if isinstance(renewal_date, str):
        try:
            renewal_date = datetime.datetime.strptime(renewal_date, "%Y-%m-%d").date()
        except ValueError:
            renewal_date = None
    renewal_date_str = renewal_date.strftime("%Y-%m-%d") if renewal_date else "unknown_date"
    return f"documents/{member_name}/{renewal_date_str}/{doc_type}/{filename}"

def or_upload_path(instance, filename):
    return document_upload_path(instance, filename, "or")

def cr_upload_path(instance, filename):
    return document_upload_path(instance, filename, "cr")

class Batch(models.Model):
    number = models.CharField(max_length=20, unique=True)
    def __str__(self):
        return f"Batch {self.number}"

class Member(models.Model):
    name = models.CharField(max_length=255)
    gmail = models.EmailField(unique=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="members")
    file_number = models.CharField(max_length=100, unique=True)
    renewal_date = models.DateField(default="2024-01-01")
    # No changes needed for Member, document is tied to Vehicle
    def __str__(self):
        return self.name

class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    engine_number = models.CharField(max_length=50, blank=True, null=True)
    chassis_number = models.CharField(max_length=50, blank=True, null=True)
    make_brand = models.CharField(max_length=100, blank=True, null=True)
    body_type = models.CharField(max_length=50, blank=True, null=True)
    year_model = models.PositiveIntegerField(blank=True, null=True)
    series = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    member = models.OneToOneField(
        'Member',
        on_delete=models.CASCADE,
        related_name="vehicle",
        null=True,
        blank=True
    )
    # Vehicle can have many documents (one per renewal)
    def __str__(self):
        return self.plate_number

class Document(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    renewal_date = models.DateField(default="2024-01-01")  # Add default here!
    official_receipt = models.ImageField(upload_to=or_upload_path, verbose_name="Official Receipt (OR)")
    certificate_of_registration = models.ImageField(upload_to=cr_upload_path, verbose_name="Certificate of Registration (CR)")

    def __str__(self):
        return f"Document for {self.vehicle.plate_number} ({self.renewal_date})"
