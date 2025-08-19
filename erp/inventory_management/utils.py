from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import STN, STNDetail


@transaction.atomic
def next_stn_code():
    """Generate next STN code in format STN-YYYY-####"""
    year = timezone.now().year
    prefix = f'STN-{year}-'
    last_stn = STN.objects.filter(stn_code__startswith=prefix).order_by('-stn_code').first()
    if last_stn:
        last_num = int(last_stn.stn_code.split('-')[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    return f'{prefix}{next_num:04d}'


def recompute_rollups(stn_id):
    """Recompute sum_created_qty from STNDetail lines"""
    from django.db.models import Sum
    stn = STN.objects.get(id=stn_id)
    total_created = stn.lines.aggregate(total=Sum('created_qty'))['total'] or Decimal('0')
    stn.sum_created_qty = total_created
    stn.save(update_fields=['sum_created_qty'])


def get_available_physical_qty(sku_id, warehouse_id):
    """Get available physical quantity for SKU in warehouse
    TODO: Integrate with warehousing inventory system
    """
    return Decimal('0')
