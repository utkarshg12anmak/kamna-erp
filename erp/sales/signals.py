from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import PriceList, PriceListItem, PriceListStatus
from .services import sync_pricelist_coverage, has_conflicts_for_pricelist

@receiver(post_save, sender=PriceList)
def _pl_saved(sender, instance: PriceList, created, **kwargs):
    sync_pricelist_coverage(instance.id)

@receiver(pre_save, sender=PriceList)
def _pl_presave_guard(sender, instance: PriceList, **kwargs):
    if instance.pk:
        prev = PriceList.objects.get(pk=instance.pk)
        if (prev.effective_from != instance.effective_from) or (prev.effective_till != instance.effective_till) or (prev.status != instance.status) or (prev.territory_id != instance.territory_id):
            conflicts = has_conflicts_for_pricelist(instance)
            if conflicts:
                raise ValidationError({'price_list': f'Conflicts detected: {conflicts[:5]} ...'})

@receiver(post_save, sender=PriceListItem)
def _pli_saved(sender, instance: PriceListItem, created, **kwargs):
    pl = instance.price_list
    conflicts = has_conflicts_for_pricelist(pl)
    if conflicts:
        raise ValidationError({'item': f'Conflicts with existing price list(s): {conflicts[:5]} ...'})
    sync_pricelist_coverage(pl.id)

@receiver(post_delete, sender=PriceListItem)
def _pli_deleted(sender, instance: PriceListItem, **kwargs):
    sync_pricelist_coverage(instance.price_list_id)
