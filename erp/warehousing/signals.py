from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Warehouse
from .services import create_standard_virtual_bins


@receiver(post_save, sender=Warehouse)
def create_bins_on_warehouse_create(sender, instance: Warehouse, created, **kwargs):
    if created:
        create_standard_virtual_bins(instance)
