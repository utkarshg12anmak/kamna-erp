from django.apps import AppConfig


class HrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hr'
    verbose_name = 'HR & Employees'
    
    def ready(self):
        from . import signals  # noqa
