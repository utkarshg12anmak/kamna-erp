from datetime import date
from django.db import transaction
from geo.models import TerritoryCoverage
from .models import PriceList, PriceListItem, PriceCoverage, PriceListStatus

def windows_overlap(a_from, a_till, b_from, b_till):
    a0 = a_from or date.min; a1 = a_till or date.max
    b0 = b_from or date.min; b1 = b_till or date.max
    return not (a1 < b0 or b1 < a0)

@transaction.atomic
def sync_pricelist_coverage(pl_id: int):
    pl = PriceList.objects.select_related('territory').get(pk=pl_id)
    pins = list(TerritoryCoverage.objects.filter(territory=pl.territory).values_list('pincode_id', flat=True))
    items = list(PriceListItem.objects.filter(price_list=pl).values_list('item_id', flat=True))
    wanted_keys = set((i, p, pl.status) for i in items for p in pins)
    # Always update all coverage rows for this price list to match the price list's dates
    PriceCoverage.objects.filter(price_list=pl).update(effective_from=pl.effective_from, effective_till=pl.effective_till)
    # Failsafe: ensure all rows for this price list have correct dates (in case of transaction/refresh issues)
    for row in PriceCoverage.objects.filter(price_list=pl):
        if row.effective_from != pl.effective_from or row.effective_till != pl.effective_till:
            row.effective_from = pl.effective_from
            row.effective_till = pl.effective_till
            row.save(update_fields=["effective_from", "effective_till"])
    # Fetch all existing coverage rows for this price list
    existing = PriceCoverage.objects.filter(price_list=pl)
    existing_keys = set((row.item_id, row.pincode_id, row.status) for row in existing)
    # Add missing rows (delete any conflicting row for (item, pincode, status) in DRAFT/PUBLISHED first)
    to_create = []
    for key in wanted_keys - existing_keys:
        i, p, status = key
        PriceCoverage.objects.filter(item_id=i, pincode_id=p, status=status).delete()
        to_create.append(PriceCoverage(item_id=i, pincode_id=p, price_list=pl, effective_from=pl.effective_from, effective_till=pl.effective_till, status=status))
    if to_create:
        PriceCoverage.objects.bulk_create(to_create, batch_size=1000)
    # Delete extra rows
    for row in existing:
        if (row.item_id, row.pincode_id, row.status) not in wanted_keys:
            row.delete()

def has_conflicts_for_pricelist(pl: PriceList) -> list:
    pins = TerritoryCoverage.objects.filter(territory=pl.territory).values_list('pincode_id', flat=True)
    conflicts = []
    for item_id in PriceListItem.objects.filter(price_list=pl).values_list('item_id', flat=True):
        qs = PriceCoverage.objects.filter(item_id=item_id, pincode_id__in=pins, status__in=[PriceListStatus.DRAFT, PriceListStatus.PUBLISHED]).exclude(price_list_id=pl.id).select_related('price_list').distinct()
        for pc in qs:
            if windows_overlap(pl.effective_from, pl.effective_till, pc.effective_from, pc.effective_till):
                conflicts.append((item_id, pc.pincode_id, pc.price_list.code))
    return conflicts
