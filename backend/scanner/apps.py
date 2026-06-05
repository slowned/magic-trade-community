from django.apps import AppConfig


class ScannerConfig(AppConfig):
    """Django app that exposes the card-scanner endpoint."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scanner'
