from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Member, PaymentType, PaymentEntry

@receiver(post_save, sender=Member)
def create_payment_entries_for_new_member(sender, instance, created, **kwargs):
    if created:  # Only run this logic when a new Member is created
        # Get all "From Members" payment types
        from_members_payment_types = PaymentType.objects.filter(payment_type='from_members')

        # Create PaymentEntry records for each payment type and month
        for payment_type in from_members_payment_types:
            for month in range(1, 13):  # January to December
                PaymentEntry.objects.create(
                    payment_type=payment_type,
                    member=instance,
                    month=month,
                    amount_paid=0.00  # Default to 0
                )