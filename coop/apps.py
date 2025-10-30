from django.apps import AppConfig


class CoopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'coop'

    def ready(self):
        import coop.signals  # Import the signals to connect them
