from django.core.management.base import BaseCommand
from coop.models import Vehicle

class Command(BaseCommand):
    help = 'Populate the Vehicle table with 10 sample instances'

    def handle(self, *args, **options):
        vehicles = [
            {
                "plate_number": f"TEST{1000+i}",
                "engine_number": f"ENG{i+1:04d}",
                "chassis_number": f"CHS{i+1:04d}",
                "make_brand": f"Brand {i%3+1}",
                "body_type": "van",
                "year_model": 2020 + i,
                "series": f"Series {chr(65+i)}",
                "color": ["Red", "Blue", "Green", "White", "Black"][i % 5],
            }
            for i in range(10)
        ]
        created = 0
        for v in vehicles:
            obj, was_created = Vehicle.objects.get_or_create(
                plate_number=v["plate_number"],
                defaults={
                    "engine_number": v["engine_number"],
                    "chassis_number": v["chassis_number"],
                    "make_brand": v["make_brand"],
                    "body_type": v["body_type"],
                    "year_model": v["year_model"],
                    "series": v["series"],
                    "color": v["color"],
                }
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'{created} vehicles populated.'))