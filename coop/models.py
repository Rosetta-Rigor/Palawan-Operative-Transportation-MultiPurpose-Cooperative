from django.db import models

class Batch(models.Model):
    number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Batch {self.number}"


class Member(models.Model):
    name = models.CharField(max_length=255)
    gmail = models.EmailField(unique=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="members")
    file_number = models.CharField(max_length=100, unique=True)
    renewal_date = models.DateField()
    # Remove vehicle_plate, use related Vehicle instead

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

    # Make member optional
    member = models.OneToOneField(
        'Member',
        on_delete=models.CASCADE,
        related_name="vehicle",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.plate_number
