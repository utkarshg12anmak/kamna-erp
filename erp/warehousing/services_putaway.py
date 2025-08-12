from decimal import Decimal
from django.db import transaction, models, IntegrityError
from django.utils import timezone
from .models import Warehouse, Location, StockLedger, MovementType, LocationType, VirtualSubtype, PutawayBatch
import uuid
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

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


class PutawayBatchGuard(Exception):
    pass

@transaction.atomic
def post_actions(warehouse: Warehouse, actions: list, user, reason_map: dict | None = None, batch_ref_id: str | None = None):
    """Post a list of actions atomically with strong idempotency.
    Idempotency: merged action set -> canonical fingerprint JSON -> sha1 digest (16 hex) -> ref 'putaway:<digest>'.
    A unique (warehouse, ref_id) PutawayBatch row is created first; IntegrityError => duplicate (no ledger rows written).
    Client can force separate batch via batch_ref_id starting with 'override:' or 'client:'."""
    if not actions:
        return {'posted_count': 0, 'batch_ref_id': None, 'duplicate': False, 'detail': 'No actions'}
    
    # Canonical merge - ensure deterministic ordering
    temp_merged: dict[tuple, Decimal] = {}
    for a in actions:
        key = (a['type'], a['item'], a['source_bin'], a.get('target_location'))
        temp_merged[key] = temp_merged.get(key, Decimal('0')) + Decimal(str(a['qty']))
    
    # Remove zero-quantity actions after merging
    merged = {k: v for k, v in temp_merged.items() if v > 0}
    if not merged:
        return {'posted_count': 0, 'batch_ref_id': None, 'duplicate': False, 'detail': 'No valid actions after merging'}
    
    # Generate fingerprint for deduplication
    fingerprint_list = [
        {'type': k[0], 'item': k[1], 'src': k[2], 'tgt': k[3], 'qty': str(qty)}
        for k, qty in merged.items()
    ]
    fingerprint_list.sort(key=lambda d: (d['type'], d['item'], d['src'], d['tgt']))
    fingerprint_raw = json.dumps(fingerprint_list, separators=(',', ':'))
    digest = hashlib.sha1(fingerprint_raw.encode()).hexdigest()[:16]
    digest_ref = f"putaway:{digest}"
    
    # Determine effective ref_id with improved logic
    if batch_ref_id:
        if batch_ref_id.startswith(('override:', 'client:')):
            # Client-provided or override key - use as-is for separate batching
            effective_ref = batch_ref_id
        else:
            # Unknown format - log warning and use digest-based deduplication
            logger.warning("putaway.post_actions ignoring unrecognized batch_ref_id format=%s; using digest_ref=%s", batch_ref_id, digest_ref)
            effective_ref = digest_ref
    else:
        # No client key - use digest-based deduplication
        effective_ref = digest_ref
    
    batch_ref_id = effective_ref
    
    # Attempt to claim batch via PutawayBatch insert with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            PutawayBatch.objects.create(warehouse=warehouse, ref_id=batch_ref_id, fingerprint=fingerprint_raw, created_by=user)
            break  # Success - batch claimed
        except IntegrityError:
            # Already exists -> treat as duplicate (no further ledger rows)
            logger.info("putaway.post_actions duplicate batch_ref_id=%s (attempt %d)", batch_ref_id, attempt + 1)
            return {'posted_count': 0, 'batch_ref_id': batch_ref_id, 'duplicate': True}
        except Exception as e:
            # Other database errors - retry with exponential backoff
            if attempt < max_retries - 1:
                import time
                time.sleep(0.1 * (2 ** attempt))  # 0.1s, 0.2s, 0.4s
                logger.warning("putaway.post_actions batch creation failed (attempt %d): %s", attempt + 1, str(e))
                continue
            else:
                # Final attempt failed
                logger.error("putaway.post_actions batch creation failed after %d attempts: %s", max_retries, str(e))
                raise PutawayBatchGuard(f"Failed to create batch after {max_retries} attempts: {str(e)}")
    
    # Lock sources to serialize qty checks and prevent race conditions
    source_ids = {src_id for (_atype, _item_id, src_id, _tgt_id) in merged.keys()}
    if source_ids:
        # Use select_for_update with nowait=False to ensure proper locking
        list(Location.objects.select_for_update().filter(id__in=source_ids).only('id'))
    # Validate availability & action semantics
    totals_by_bin_item: dict[tuple, Decimal] = {}
    for (atype, item_id, src_id, tgt_id), qty in merged.items():
        k2 = (item_id, src_id)
        totals_by_bin_item[k2] = totals_by_bin_item.get(k2, Decimal('0')) + qty
    for (item_id, src_id), total_qty in totals_by_bin_item.items():
        available = on_hand_qty(warehouse.id, src_id, item_id)
        if total_qty > available:
            raise ValueError(f"Insufficient qty in bin; requested={total_qty} available={available}")
    for (atype, item_id, src_id, tgt_id), qty in merged.items():
        validate_action(warehouse, {'type': atype, 'item': item_id, 'source_bin': src_id, 'qty': qty, 'target_location': tgt_id})
    # Post ledger rows
    posted_groups = 0
    for (atype, item_id, src_id, tgt_id), qty in merged.items():
        src = Location.objects.get(id=src_id)
        if atype == 'PUTAWAY':
            tgt = Location.objects.get(id=tgt_id)
            memo = (reason_map or {}).get(str(src.subtype), 'putaway')
            StockLedger.objects.create(warehouse=warehouse, location=src, item_id=item_id, qty_delta=-qty, movement_type=MovementType.PUTAWAY, ref_model='PUTAWAY', ref_id=batch_ref_id, user=user, memo=memo)
            StockLedger.objects.create(warehouse=warehouse, location=tgt, item_id=item_id, qty_delta=+qty, movement_type=MovementType.PUTAWAY, ref_model='PUTAWAY', ref_id=batch_ref_id, user=user, memo=memo)
        else:
            lost_bin = get_virtual(warehouse, VirtualSubtype.LOST)
            StockLedger.objects.create(warehouse=warehouse, location=src, item_id=item_id, qty_delta=-qty, movement_type=MovementType.PUTAWAY_LOST, ref_model='PUTAWAY', ref_id=batch_ref_id, user=user, memo='lost via putaway')
            StockLedger.objects.create(warehouse=warehouse, location=lost_bin, item_id=item_id, qty_delta=+qty, movement_type=MovementType.PUTAWAY_LOST, ref_model='PUTAWAY', ref_id=batch_ref_id, user=user, memo='lost via putaway')
        posted_groups += 1
    logger.info("putaway.post_actions posted_count=%s batch_ref_id=%s", posted_groups, batch_ref_id)
    return {'posted_count': posted_groups, 'batch_ref_id': batch_ref_id, 'duplicate': False}
