from django.apps import AppConfig


class InventoryManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory_management"
    verbose_name = "Inventory Management"

    def ready(self):
        from . import signals
