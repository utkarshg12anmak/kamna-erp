from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from .models import Warehouse, Location, StockLedger, MovementType, LocationType, VirtualSubtype
import uuid

# Compute on-hand by summing ledger

def on_hand_qty(warehouse_id: int, location_id: int, item_id: int) -> Decimal:
    qs = StockLedger.objects.filter(warehouse_id=warehouse_id, location_id=location_id, item_id=item_id)
    agg = qs.aggregate(total=models.Sum('qty_delta'))
    return agg['total'] or Decimal('0')

# Resolve required virtual bins

def get_virtual(warehouse: Warehouse, subtype_slug: str) -> Location:
    return Location.objects.get(warehouse=warehouse, type=LocationType.VIRTUAL, subtype=subtype_slug)

# Validate a single action

def validate_action(warehouse: Warehouse, action: dict):
    atype = action.get('type')  # 'PUTAWAY' or 'LOST'
    item_id = action.get('item')
    source_id = action.get('source_bin')
    qty = Decimal(str(action.get('qty')))
    if qty <= 0:
        raise ValueError('Quantity must be > 0')
    # source must be Return or Receive
    src = Location.objects.select_related('warehouse').get(id=source_id, warehouse=warehouse)
    if src.type != LocationType.VIRTUAL or src.subtype not in (VirtualSubtype.RETURN, VirtualSubtype.RECEIVE):
        raise ValueError('Source must be Return or Receive bin in this warehouse')
    # cap by bin qty
    available = on_hand_qty(warehouse.id, src.id, item_id)
    if qty > available:
        raise ValueError(f'Insufficient qty in bin; available={available}')
    if atype == 'PUTAWAY':
        tgt_id = action.get('target_location')
        tgt = Location.objects.get(id=tgt_id, warehouse=warehouse)
        if tgt.type != LocationType.PHYSICAL:
            raise ValueError('Target must be a PHYSICAL location')
        if tgt.status != 'ACTIVE':
            raise ValueError('Target location is not ACTIVE')
    elif atype == 'LOST':
        pass
    else:
        raise ValueError('Invalid action type')


@transaction.atomic
def post_actions(warehouse: Warehouse, actions: list, user, reason_map: dict | None = None, batch_ref_id: str | None = None):
    """Post a list of actions atomically. Each action: {type, item, source_bin, qty, target_location?}
    reason_map: optional mapping of source bin subtype -> memo ('return putaway'/'receive putaway')."""
    # Create a batch reference for this confirm to aid grouping/debugging and duplicate detection upstream
    batch_ref_id = batch_ref_id or f"putaway:{timezone.now().isoformat()}:{uuid.uuid4().hex[:8]}"
    # Idempotency: if this ref already exists, skip posting
    if StockLedger.objects.filter(warehouse=warehouse, ref_model='PUTAWAY', ref_id=batch_ref_id).exists():
        return {'posted_count': 0, 'batch_ref_id': batch_ref_id, 'duplicate': True}
    # Merge by (type,item,source_bin,target_location)
    merged: dict[tuple, Decimal] = {}
    for a in actions:
        key = (a['type'], a['item'], a['source_bin'], a.get('target_location'))
        merged[key] = merged.get(key, Decimal('0')) + Decimal(str(a['qty']))
    # Concurrency validation: total per (item, source_bin) cannot exceed available
    totals_by_bin_item: dict[tuple, Decimal] = {}
    for (atype, item_id, src_id, tgt_id), qty in merged.items():
        k2 = (item_id, src_id)
        totals_by_bin_item[k2] = totals_by_bin_item.get(k2, Decimal('0')) + qty
    for (item_id, src_id), total_qty in totals_by_bin_item.items():
        # on-hand available at source at the time of posting
        available = on_hand_qty(warehouse.id, src_id, item_id)
        if total_qty > available:
            raise ValueError(f"Insufficient qty in bin; requested={total_qty} available={available}")
    # Validate each merged action (ensures target validity etc.)
    for (atype, item_id, src_id, tgt_id), qty in merged.items():
        validate_action(warehouse, {'type': atype, 'item': item_id, 'source_bin': src_id, 'qty': qty, 'target_location': tgt_id})
    # Post
    for (atype, item_id, src_id, tgt_id), qty in merged.items():
        src = Location.objects.get(id=src_id)
        if atype == 'PUTAWAY':
            tgt = Location.objects.get(id=tgt_id)
            memo = (reason_map or {}).get(str(src.subtype), 'putaway')
            # − from src, + to tgt
            StockLedger.objects.create(warehouse=warehouse, location=src, item_id=item_id, qty_delta=-qty, movement_type=MovementType.PUTAWAY, ref_model='PUTAWAY', ref_id=batch_ref_id, user=user, memo=memo)
            StockLedger.objects.create(warehouse=warehouse, location=tgt, item_id=item_id, qty_delta=+qty, movement_type=MovementType.PUTAWAY, ref_model='PUTAWAY', ref_id=batch_ref_id, user=user, memo=memo)
        else:  # LOST
            lost_bin = get_virtual(warehouse, VirtualSubtype.LOST)
            StockLedger.objects.create(warehouse=warehouse, location=src, item_id=item_id, qty_delta=-qty, movement_type=MovementType.PUTAWAY_LOST, ref_model='PUTAWAY', ref_id=batch_ref_id, user=user, memo='lost via putaway')
            StockLedger.objects.create(warehouse=warehouse, location=lost_bin, item_id=item_id, qty_delta=+qty, movement_type=MovementType.PUTAWAY_LOST, ref_model='PUTAWAY', ref_id=batch_ref_id, user=user, memo='lost via putaway')
    return {'posted_count': len(merged), 'batch_ref_id': batch_ref_id, 'duplicate': False}
