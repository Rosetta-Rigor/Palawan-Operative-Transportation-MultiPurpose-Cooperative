from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser GTX1050TI with password GTX1050TI (full authority)'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'GTX1060TI'
        password = 'GTX1060TI'
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, password=password, email='gtx1050ti@example.com')
            user.role = 'superadmin'
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superadmin {username} created with password {password}'))
        else:
            self.stdout.write(self.style.WARNING(f'User {username} already exists'))
