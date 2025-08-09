from django.apps import AppConfig


class WarehousingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "warehousing"

    def ready(self):
        # Import signals to register handlers
        from . import signals  # noqa: F401
