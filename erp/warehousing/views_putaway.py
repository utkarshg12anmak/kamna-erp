# filepath: /Users/dealshare/Documents/GitHub/kamna-erp/erp/warehousing/views_putaway.py
from decimal import Decimal
from typing import List, Dict, Any
from django.db.models import Sum, Max, Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response
from .models import Warehouse, Location, LocationType, VirtualSubtype, StockLedger
from .serializers_putaway import PutawayListRowSerializer, PutawayBatchSerializer
from .services_putaway import post_actions


@api_view(["GET"])  # KPIs for Putaway (RETURN/RECEIVE bins)
@permission_classes([permissions.IsAuthenticated])
def putaway_kpis(request, pk: int):
    # Require view permission on StockLedger
    _ = request.user  # noqa
    wh = get_object_or_404(Warehouse, pk=pk)
    vsubtypes = [VirtualSubtype.RETURN, VirtualSubtype.RECEIVE]
    base = (
        StockLedger.objects.filter(
            warehouse=wh, location__type=LocationType.VIRTUAL, location__subtype__in=vsubtypes
        )
    )
    agg = (
        base.values("location__subtype")
        .annotate(total_qty=Sum("qty_delta"), last_moved_at=Max("ts"))
    )
    # Compute distinct items with stock per subtype
    items_per_subtype = {}
    for sub in vsubtypes:
        per = (
            base.filter(location__subtype=sub)
            .values("item_id")
            .annotate(q=Sum("qty_delta"))
        )
        items_per_subtype[sub] = sum(1 for r in per if (r.get("q") or 0) != 0)
    result = {
        "warehouse": wh.id,
        "return": {"qty": 0.0, "items": 0, "last_moved_at": None},
        "receive": {"qty": 0.0, "items": 0, "last_moved_at": None},
        "total_qty": 0.0,
        "total_items": 0,
    }
    total_items_set = set()
    for row in agg:
        q = float(row.get("total_qty") or 0)
        sub = row.get("location__subtype")
        if sub == VirtualSubtype.RETURN:
            result["return"]["qty"] = q
            result["return"]["items"] = int(items_per_subtype[VirtualSubtype.RETURN])
            result["return"]["last_moved_at"] = row.get("last_moved_at")
        elif sub == VirtualSubtype.RECEIVE:
            result["receive"]["qty"] = q
            result["receive"]["items"] = int(items_per_subtype[VirtualSubtype.RECEIVE])
            result["receive"]["last_moved_at"] = row.get("last_moved_at")
        result["total_qty"] += q
    # Total distinct items across both subtypes
    per_item = base.values("item_id").annotate(q=Sum("qty_delta"))
    for r in per_item:
        if float(r.get("q") or 0) != 0:
            total_items_set.add(int(r["item_id"]))
    result["total_items"] = len(total_items_set)
    return Response(result)


@api_view(["GET"])  # List available putaway rows grouped by (item, bin)
@permission_classes([permissions.IsAuthenticated])
def putaway_list(request, pk: int):
    wh = get_object_or_404(Warehouse, pk=pk)
    vsubtypes = [VirtualSubtype.RETURN, VirtualSubtype.RECEIVE]
    base = StockLedger.objects.filter(
        warehouse=wh, location__type=LocationType.VIRTUAL, location__subtype__in=vsubtypes
    )
    # Filters
    q = request.GET.get("q")
    brand = request.GET.get("brand")
    category = request.GET.get("category")
    bin_id = request.GET.get("bin")
    subtype = request.GET.get("subtype")

    if q:
        base = base.filter(Q(item__sku__icontains=q) | Q(item__name__icontains=q))
    if brand:
        try:
            base = base.filter(item__brand_id=int(brand))
        except Exception:
            pass
    if category:
        try:
            base = base.filter(item__category_id=int(category))
        except Exception:
            pass
    if bin_id:
        try:
            base = base.filter(location_id=int(bin_id))
        except Exception:
            pass
    if subtype:
        base = base.filter(location__subtype=subtype)

    qs = (
        base
        .values(
            "item_id",
            "item__sku",
            "item__name",
            "item__image",
            "location_id",
            "location__display_name",
        )
        .annotate(q=Sum("qty_delta"), last_moved_at=Max("ts"))
        .order_by("item__sku", "location_id")
    ).filter(q__gt=0)

    rows = []
    for r in qs:
        img_url = ""
        try:
            if r.get("item__image"):
                from django.conf import settings
                media_url = getattr(settings, "MEDIA_URL", "/media/")
                img_url = f"{media_url}{r['item__image']}"
        except Exception:
            img_url = ""
        rows.append({
            "item_id": int(r["item_id"]),
            "sku": r["item__sku"],
            "name": r["item__name"],
            "img": img_url,
            "bin_location_id": int(r["location_id"]),
            "bin": r.get("location__display_name") or "",
            "qty": r["q"],
            "last_moved_at": r.get("last_moved_at"),
        })
    ser = PutawayListRowSerializer(rows, many=True)
    return Response({"results": ser.data})


@api_view(["POST"])  # Confirm putaway batch
@permission_classes([permissions.IsAuthenticated])
def putaway_confirm(request, pk: int):
    wh = get_object_or_404(Warehouse, pk=pk)
    ser = PutawayBatchSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    actions = ser.validated_data.get("actions", [])
    idempotency_key = ser.validated_data.get("idempotency_key") or None
    # Defensive: collapse any duplicate identical actions client-side did not merge (extra safety)
    collapsed = {}
    for a in actions:
        key = (a['type'], a['item'], a['source_bin'], a.get('target_location'))
        collapsed[key] = collapsed.get(key, Decimal('0')) + a['qty']
    normalized_actions = []
    for (t,i,s,tgt), qty in collapsed.items():
        d = {'type':t,'item':i,'source_bin':s,'qty':qty}
        if t=='PUTAWAY': d['target_location']=tgt
        normalized_actions.append(d)
    actions = normalized_actions
    try:
        result = post_actions(
            warehouse=wh,
            actions=actions,
            user=request.user,
            reason_map={
                str(VirtualSubtype.RETURN): "return putaway",
                str(VirtualSubtype.RECEIVE): "receive putaway",
            },
            batch_ref_id=idempotency_key,
        )
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"ok": True, **result})
