from django.core.management.base import BaseCommand
from coop.models import Member, Batch
import random

class Command(BaseCommand):
    help = 'Populate the Member table with 20 sample members'

    def handle(self, *args, **options):
        first_names = [
            "Juan", "Maria", "Jose", "Ana", "Pedro", "Luisa", "Carlos", "Rosa", "Miguel", "Elena",
            "Antonio", "Carmen", "Luis", "Teresa", "Jorge", "Patricia", "Ricardo", "Gloria", "Manuel", "Isabel"
        ]
        last_names = [
            "Santos", "Reyes", "Cruz", "Bautista", "Garcia", "Lopez", "Torres", "Ramos", "Mendoza", "Flores"
        ]

        # Get or create a Batch to assign members to
        batch, _ = Batch.objects.get_or_create(number="BATCH-001")

        created = 0
        for i in range(20):
            full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            batch_monitoring_number = i + 1
            member, was_created = Member.objects.get_or_create(
                full_name=full_name,
                batch=batch,
                batch_monitoring_number=batch_monitoring_number
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'{created} members populated.'))