from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from .models import (
    Location,
    LocationType,
    VirtualSubtype,
    WarehouseStatus,
    StockLedger,
    MovementType,
    AdjustmentRequest,
    AdjustmentStatus,
    AdjustmentType,  # added
)


def ensure_location_empty(location_id: int) -> bool:
    """Check if a location has zero on-hand across all items.
    Returns True when empty (safe to deactivate), False otherwise.
    """
    total = (
        StockLedger.objects.filter(location_id=location_id)
        .values("item_id")
        .annotate(q=Sum("qty_delta"))
        .aggregate(total=Sum("q"))
        .get("total")
    )
    return (total or Decimal("0")) == 0


def get_virtual(warehouse, subtype_slug: str) -> Location:
    try:
        return Location.objects.get(
            warehouse=warehouse, type=LocationType.VIRTUAL, subtype=subtype_slug
        )
    except Location.DoesNotExist:
        # Attempt to auto-provision standard virtual bins, then retry
        try:
            create_standard_virtual_bins(warehouse)
            return Location.objects.get(
                warehouse=warehouse, type=LocationType.VIRTUAL, subtype=subtype_slug
            )
        except Exception:
            raise ValidationError(
                f"Virtual bin '{subtype_slug}' not found for warehouse {warehouse.code}"
            )


def on_hand_qty(warehouse_id: int, location_id: int, item_id: int) -> Decimal:
    agg = (
        StockLedger.objects.filter(
            warehouse_id=warehouse_id, location_id=location_id, item_id=item_id
        ).aggregate(total=Sum("qty_delta"))
    )
    return agg.get("total") or Decimal("0")


@transaction.atomic
def post_ledger(
    *,
    warehouse,
    from_location: Location | None,
    to_location: Location | None,
    item,
    qty: Decimal,
    movement_type: str,
    user,
    ref_model: str = "",
    ref_id: str = "",
    memo: str = "",
):
    if qty <= 0:
        raise ValidationError("qty must be > 0")
    if from_location is None and to_location is None:
        raise ValidationError("Either from_location or to_location is required")

    if from_location is not None:
        StockLedger.objects.create(
            warehouse=warehouse,
            location=from_location,
            item=item,
            qty_delta=Decimal(qty) * Decimal("-1"),
            movement_type=movement_type,
            ref_model=ref_model,
            ref_id=str(ref_id or ""),
            memo=memo,
            user=user,
        )

    if to_location is not None:
        StockLedger.objects.create(
            warehouse=warehouse,
            location=to_location,
            item=item,
            qty_delta=Decimal(qty),
            movement_type=movement_type,
            ref_model=ref_model,
            ref_id=str(ref_id or ""),
            memo=memo,
            user=user,
        )


@transaction.atomic
def request_post_moves(adjr: AdjustmentRequest, user):
    wh = adjr.warehouse
    item = adjr.item
    qty = adjr.qty
    ref = ("warehousing.AdjustmentRequest", adjr.id)

    if AdjustmentType is None:  # safeguard (no-op, keeps context concise)
        pass
    # Replace adjr.AdjustmentType.* with AdjustmentType.*
    if adjr.type == AdjustmentType.DAMAGE:
        src = adjr.source_location
        if on_hand_qty(wh.id, src.id, item.id) < qty:
            raise ValidationError("Insufficient stock for DAMAGE request")
        dst = get_virtual(wh, VirtualSubtype.DAMAGE_PENDING)
        post_ledger(
            warehouse=wh,
            from_location=src,
            to_location=dst,
            item=item,
            qty=qty,
            movement_type=MovementType.ADJ_REQ_DAMAGE,
            user=user,
            ref_model=ref[0],
            ref_id=str(ref[1]),
            memo=adjr.memo or "",
        )
    elif adjr.type == AdjustmentType.LOST:
        src = adjr.source_location
        if on_hand_qty(wh.id, src.id, item.id) < qty:
            raise ValidationError("Insufficient stock for LOST request")
        dst = get_virtual(wh, VirtualSubtype.LOST_PENDING)
        post_ledger(
            warehouse=wh,
            from_location=src,
            to_location=dst,
            item=item,
            qty=qty,
            movement_type=MovementType.ADJ_REQ_LOST,
            user=user,
            ref_model="warehousing.AdjustmentRequest",
            ref_id=str(adjr.id),
            memo=adjr.memo or "",
        )
    elif adjr.type == AdjustmentType.EXCESS:
        dst = get_virtual(wh, VirtualSubtype.EXCESS_PENDING)
        post_ledger(
            warehouse=wh,
            from_location=None,
            to_location=dst,
            item=item,
            qty=qty,
            movement_type=MovementType.ADJ_REQ_EXCESS,
            user=user,
            ref_model="warehousing.AdjustmentRequest",
            ref_id=str(adjr.id),
            memo=adjr.memo or "",
        )
    else:
        raise ValidationError("Unknown adjustment type")


@transaction.atomic
def approve_post_moves(adjr: AdjustmentRequest, user):
    wh = adjr.warehouse
    item = adjr.item
    qty = adjr.qty
    if adjr.type == AdjustmentType.DAMAGE:
        src = get_virtual(wh, VirtualSubtype.DAMAGE_PENDING)
        dst = get_virtual(wh, VirtualSubtype.DAMAGE)
        post_ledger(
            warehouse=wh,
            from_location=src,
            to_location=dst,
            item=item,
            qty=qty,
            movement_type=MovementType.ADJ_APPROVE_DAMAGE,
            user=user,
            ref_model="warehousing.AdjustmentRequest",
            ref_id=str(adjr.id),
            memo=adjr.memo or "",
        )
    elif adjr.type == AdjustmentType.LOST:
        src = get_virtual(wh, VirtualSubtype.LOST_PENDING)
        dst = get_virtual(wh, VirtualSubtype.LOST)
        post_ledger(
            warehouse=wh,
            from_location=src,
            to_location=dst,
            item=item,
            qty=qty,
            movement_type=MovementType.ADJ_APPROVE_LOST,
            user=user,
            ref_model="warehousing.AdjustmentRequest",
            ref_id=str(adjr.id),
            memo=adjr.memo or "",
        )
    elif adjr.type == AdjustmentType.EXCESS:
        src = get_virtual(adjr.warehouse, VirtualSubtype.EXCESS_PENDING)
        dst = get_virtual(adjr.warehouse, VirtualSubtype.RETURN)
        post_ledger(
            warehouse=wh,
            from_location=src,
            to_location=dst,
            item=item,
            qty=qty,
            movement_type=MovementType.ADJ_APPROVE_EXCESS,
            user=user,
            ref_model="warehousing.AdjustmentRequest",
            ref_id=str(adjr.id),
            memo=adjr.memo or "",
        )
    else:
        raise ValidationError("Unknown adjustment type")


@transaction.atomic
def decline_post_moves(adjr: AdjustmentRequest, user):
    wh = adjr.warehouse
    item = adjr.item
    qty = adjr.qty
    if adjr.type == AdjustmentType.DAMAGE:
        src = get_virtual(wh, VirtualSubtype.DAMAGE_PENDING)
        dst = get_virtual(wh, VirtualSubtype.RETURN)
        post_ledger(
            warehouse=wh,
            from_location=src,
            to_location=dst,
            item=item,
            qty=qty,
            movement_type=MovementType.ADJ_DECLINE_DAMAGE,
            user=user,
            ref_model="warehousing.AdjustmentRequest",
            ref_id=str(adjr.id),
            memo=adjr.memo or "damage request declined",
        )
    elif adjr.type == AdjustmentType.LOST:
        src = get_virtual(wh, VirtualSubtype.LOST_PENDING)
        dst = get_virtual(wh, VirtualSubtype.RETURN)
        post_ledger(
            warehouse=wh,
            from_location=src,
            to_location=dst,
            item=item,
            qty=qty,
            movement_type=MovementType.ADJ_DECLINE_LOST,
            user=user,
            ref_model="warehousing.AdjustmentRequest",
            ref_id=str(adjr.id),
            memo=adjr.memo or "lost request declined",
        )
    elif adjr.type == AdjustmentType.EXCESS:
        # No movement on decline of EXCESS
        return
    else:
        raise ValidationError("Unknown adjustment type")


def create_standard_virtual_bins(warehouse):
    subtypes = [
        VirtualSubtype.RECEIVE,
        VirtualSubtype.DISPATCH,
        VirtualSubtype.RETURN,
        VirtualSubtype.QC,
        VirtualSubtype.HOLD,
        VirtualSubtype.DAMAGE,
        VirtualSubtype.LOST,
        VirtualSubtype.EXCESS,
        VirtualSubtype.LOST_PENDING,
        VirtualSubtype.EXCESS_PENDING,
        VirtualSubtype.DAMAGE_PENDING,
    ]
    created = 0
    for st in subtypes:
        obj, was_created = Location.objects.get_or_create(
            warehouse=warehouse,
            type=LocationType.VIRTUAL,
            subtype=st,
            defaults={
                "display_name": st.replace("_", " ").title(),
                "system_managed": True,
                "status": WarehouseStatus.ACTIVE,
            },
        )
        if was_created:
            created += 1
    return created
