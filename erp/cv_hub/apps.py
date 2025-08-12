from django.apps import AppConfig


class CvHubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cv_hub'
    verbose_name = 'Customer & Vendor Hub'
    
    def ready(self):
        from . import signals
