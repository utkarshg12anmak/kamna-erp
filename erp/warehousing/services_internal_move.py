from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import StockLedger, MovementType, Location, LocationType, Warehouse, WarehouseStatus
from .services import on_hand_qty


@dataclass(frozen=True)
class InternalMoveLine:
    item_id: int
    source_location_id: int
    target_location_id: int
    qty: Decimal


def _ensure_same_wh(loc_ids: Iterable[int]) -> int:
    wh_id = None
    locs = Location.objects.filter(id__in=list(loc_ids)).select_related("warehouse")
    if locs.count() != len(set(loc_ids)):
        raise ValidationError("Invalid location(s)")
    for l in locs:
        if l.type != LocationType.PHYSICAL:
            raise ValidationError("Locations must be PHYSICAL")
        if wh_id is None:
            wh_id = l.warehouse_id
        elif wh_id != l.warehouse_id:
            raise ValidationError("All locations must belong to the same warehouse")
    if wh_id is None:
        raise ValidationError("No locations provided")
    return wh_id


def merge_lines(lines: List[InternalMoveLine]) -> List[InternalMoveLine]:
    bucket = {}
    for ln in lines:
        key = (ln.item_id, ln.source_location_id, ln.target_location_id)
        bucket[key] = bucket.get(key, Decimal("0")) + Decimal(ln.qty)
    merged: List[InternalMoveLine] = []
    for (item, src, dst), q in bucket.items():
        if q <= 0:
            continue
        merged.append(InternalMoveLine(item_id=item, source_location_id=src, target_location_id=dst, qty=q))
    return merged


def _validate_locations(warehouse: Warehouse, from_id: int, to_id: int):
    f = Location.objects.select_related("warehouse").get(id=from_id)
    t = Location.objects.select_related("warehouse").get(id=to_id)
    if f.warehouse_id != warehouse.id or t.warehouse_id != warehouse.id:
        raise ValidationError("Locations must be in this warehouse")
    if f.type != LocationType.PHYSICAL or t.type != LocationType.PHYSICAL:
        raise ValidationError("Both locations must be PHYSICAL")
    if f.status != WarehouseStatus.ACTIVE or t.status != WarehouseStatus.ACTIVE:
        raise ValidationError("Both locations must be ACTIVE")
    if f.id == t.id:
        raise ValidationError("From and To cannot be the same")
    return f, t


@transaction.atomic
def post_internal_move(user, lines: List[InternalMoveLine], *, batch_ref_id: str | None = None) -> dict:
    if not lines:
        return {"posted": 0, "batch_ref_id": batch_ref_id or ""}
    # Validate locations, same warehouse
    wh_id = _ensure_same_wh([x.source_location_id for x in lines] + [x.target_location_id for x in lines])
    warehouse = Warehouse.objects.get(id=wh_id)

    # Idempotency: if batch_ref_id present and any ledger with that ref exists, treat as duplicate
    if batch_ref_id:
        exists = StockLedger.objects.filter(warehouse_id=wh_id, ref_model="INTERNAL_MOVE", ref_id=str(batch_ref_id)).exists()
        if exists:
            return {"posted": 0, "batch_ref_id": batch_ref_id, "duplicate": True}

    # Merge lines per (item, src, dst)
    merged = merge_lines(lines)

    # Stock checks per (item, src)
    need = {}
    for ln in merged:
        key = (ln.item_id, ln.source_location_id)
        need[key] = need.get(key, Decimal("0")) + Decimal(ln.qty)
    for (item_id, src_id), req in need.items():
        available = on_hand_qty(wh_id, src_id, item_id)
        if Decimal(available) < Decimal(req):
            raise ValidationError(f"Insufficient stock at location {src_id} for item {item_id}. Need {req}, have {available}")

    # Post entries
    posted = 0
    for ln in merged:
        StockLedger.objects.create(
            warehouse=warehouse,
            location_id=ln.source_location_id,
            item_id=ln.item_id,
            qty_delta=Decimal(ln.qty) * Decimal("-1"),
            movement_type=MovementType.INTERNAL_TRANSFER,
            ref_model="INTERNAL_MOVE",
            ref_id=str(batch_ref_id or ""),
            memo="internal move",
            user=user,
        )
        StockLedger.objects.create(
            warehouse=warehouse,
            location_id=ln.target_location_id,
            item_id=ln.item_id,
            qty_delta=Decimal(ln.qty),
            movement_type=MovementType.INTERNAL_TRANSFER,
            ref_model="INTERNAL_MOVE",
            ref_id=str(batch_ref_id or ""),
            memo="internal move",
            user=user,
        )
        posted += 2

    return {"posted": posted, "batch_ref_id": batch_ref_id or ""}


@transaction.atomic
def post_internal_move_rows(warehouse: Warehouse, from_id: int, to_id: int, lines: list[dict], user, memo: str | None = None):
    """lines = [{ 'item': <int>, 'qty': <decimal/str> }, ...]
    Merge per item, validate against current on-hand at FROM, then post all as one atomic batch.
    Returns {'ok': True, 'moved_lines': N, 'total_qty': Decimal} or {'ok': False, 'errors': {item_id: 'available=X, requested=Y'}}.
    """
    f, t = _validate_locations(warehouse, from_id, to_id)
    # merge & sanitize
    merged: dict[int, Decimal] = {}
    for ln in lines or []:
        item_id = int(ln.get('item'))
        try:
            qty = Decimal(str(ln.get('qty', '0')))
        except Exception:
            qty = Decimal('0')
        if qty <= 0:
            continue
        merged[item_id] = merged.get(item_id, Decimal('0')) + qty
    if not merged:
        return {'ok': False, 'errors': {'_form': 'No quantities entered'}}
    # availability check
    errs: dict[str, str] = {}
    for item_id, req in merged.items():
        avail = on_hand_qty(warehouse.id, f.id, item_id)
        if Decimal(req) > Decimal(avail or 0):
            errs[str(item_id)] = f'available={avail}, requested={req}'
    if errs:
        return {'ok': False, 'errors': errs}
    # post
    total = Decimal('0')
    for item_id, qty in merged.items():
        StockLedger.objects.create(warehouse=warehouse, location=f, item_id=item_id, qty_delta=-qty, movement_type=MovementType.INTERNAL_TRANSFER, ref_model='INTERNAL_MOVE', memo=memo or 'internal transfer', user=user)
        StockLedger.objects.create(warehouse=warehouse, location=t, item_id=item_id, qty_delta=+qty, movement_type=MovementType.INTERNAL_TRANSFER, ref_model='INTERNAL_MOVE', memo=memo or 'internal transfer', user=user)
        total += qty
    return {'ok': True, 'moved_lines': len(merged), 'total_qty': str(total)}
