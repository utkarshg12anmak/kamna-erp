from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import STN, STNDetail, STNStatusHistory
from .utils import next_stn_code, recompute_rollups


@receiver(pre_save, sender=STN)
def stn_pre_save(sender, instance, **kwargs):
    """Generate STN code and validate warehouses"""
    if not instance.stn_code:
        instance.stn_code = next_stn_code()
    
    if instance.source_warehouse_id == instance.destination_warehouse_id:
        raise ValidationError("Source and destination warehouse cannot be the same")


@receiver(post_save, sender=STNDetail)
def stn_detail_post_save(sender, instance, created, **kwargs):
    """Recompute rollups when STN detail is saved"""
    recompute_rollups(instance.stn_id)


@receiver(post_save, sender=STN)
def stn_post_save(sender, instance, created, **kwargs):
    """Create initial status history on STN creation"""
    if created:
        STNStatusHistory.objects.create(
            stn=instance,
            from_status=None,
            to_status=instance.status,
            changed_by=instance.created_by
        )
