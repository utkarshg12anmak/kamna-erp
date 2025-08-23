from django.apps import AppConfig


class GeoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'geo'
    verbose_name = 'Geo (State/City/Pincode)'
    
    def ready(self):
        """Import signals when app is ready."""
        from . import signals
