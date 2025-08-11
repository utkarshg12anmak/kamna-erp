from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Warehouse, StockLedger, LocationType
from .serializers_internal_move import StockRowSerializer, InternalMovePayloadSerializer, FromStockRowSerializer, RowMovePayloadSerializer
from .services_internal_move import InternalMoveLine, post_internal_move, post_internal_move_rows
from catalog.models import Item


@api_view(["GET"])  # List on-hand stock by item at a physical location for a warehouse
@permission_classes([permissions.IsAuthenticated])
def internal_move_from_location_stock(request, pk: int):
    wh = get_object_or_404(Warehouse, pk=pk)
    # Filter: only PHYSICAL locations
    qs = (
        StockLedger.objects
        .filter(warehouse=wh, location__type=LocationType.PHYSICAL)
        .values("item_id", "item__sku", "item__name", "location_id", "location__code", "location__display_name")
        .annotate(q=Sum("qty_delta"))
        .filter(q__gt=0)
        .order_by("item__sku", "location_id")
    )
    rows = []
    for r in qs:
        rows.append({
            "item": int(r["item_id"]),
            "item_sku": r["item__sku"],
            "item_name": r["item__name"],
            "location": int(r["location_id"]),
            "location_code": r.get("location__code") or "",
            "location_name": r.get("location__display_name") or "",
            "qty": r["q"],
        })
    ser = StockRowSerializer(rows, many=True)
    return Response({"results": ser.data})


@api_view(["POST"])  # Confirm internal move
@permission_classes([permissions.IsAuthenticated])
def internal_move_confirm(request, pk: int):
    wh = get_object_or_404(Warehouse, pk=pk)
    _ = wh  # not used, but ensures 404 if missing
    # Permission: require add permission on StockLedger to post internal movements
    if not request.user.has_perm("warehousing.add_stockledger"):
        return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    ser = InternalMovePayloadSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    lines = []
    for ln in ser.validated_data.get("lines", []):
        lines.append(InternalMoveLine(
            item_id=int(ln["item"]),
            source_location_id=int(ln["source_location"]),
            target_location_id=int(ln["target_location"]),
            qty=ln["qty"],
        ))
    idem = ser.validated_data.get("idempotency_key") or None
    try:
        result = post_internal_move(request.user, lines, batch_ref_id=idem)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"ok": True, **result})


@api_view(["GET"])  # Permissions for Internal Move UI
@permission_classes([permissions.IsAuthenticated])
def internal_move_permissions(request, pk: int):
    # Simple: require add permission on StockLedger
    can_confirm = request.user.has_perm("warehousing.add_stockledger")
    return Response({"can_confirm": bool(can_confirm)})


class FromStockList(APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    queryset = StockLedger.objects.all()

    def get(self, request, pk):
        try:
            wh_id = int(pk)
            loc_id = int(request.GET.get('location'))
        except Exception:
            return Response({'detail': 'location is required and must be int'}, status=status.HTTP_400_BAD_REQUEST)
        # Only PHYSICAL ACTIVE
        if not StockLedger.objects.filter(warehouse_id=wh_id, location_id=loc_id, location__type=LocationType.PHYSICAL).exists():
            return Response({'results': [], 'count': 0, 'page': 1, 'page_size': 0})
        q = (request.GET.get('q') or '').strip()
        brand = request.GET.get('brand')
        category = request.GET.get('category')
        page = max(1, int(request.GET.get('page') or 1))
        page_size = max(1, min(100, int(request.GET.get('page_size') or 25)))
        # Aggregate on-hand at loc
        base = (
            StockLedger.objects
            .filter(warehouse_id=wh_id, location_id=loc_id)
            .values('item_id')
            .annotate(on_hand=Sum('qty_delta'))
            .filter(on_hand__gt=0)
        )
        item_ids = [r['item_id'] for r in base]
        items = Item.objects.filter(id__in=item_ids)
        if q:
            items = items.filter(Q(sku__icontains=q) | Q(name__icontains=q))
        if brand:
            items = items.filter(brand_id=brand)
        if category:
            items = items.filter(category_id=category)
        items = items.order_by('sku')
        total = items.count()
        start = (page-1)*page_size
        end = start + page_size
        items_page = list(items[start:end])
        # map on_hand
        on_map = {r['item_id']: r['on_hand'] for r in base}
        rows = []
        for it in items_page:
            rows.append({
                'item_id': it.id,
                'sku': it.sku,
                'name': it.name,
                'img': (it.image.url if getattr(it, 'image', None) else None),
                'on_hand': on_map.get(it.id) or 0,
            })
        ser = FromStockRowSerializer(rows, many=True)
        return Response({'results': ser.data, 'count': total, 'page': page, 'page_size': page_size})


class ConfirmRowMove(APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    queryset = StockLedger.objects.all()

    def post(self, request, pk):
        ser = RowMovePayloadSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        wh = get_object_or_404(Warehouse, pk=pk)
        res = post_internal_move_rows(
            warehouse=wh,
            from_id=ser.validated_data['from_location'],
            to_id=ser.validated_data['to_location'],
            lines=ser.validated_data['lines'],
            user=request.user,
            memo=ser.validated_data.get('memo') or None,
        )
        if not res.get('ok'):
            return Response({'errors': res.get('errors')}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'moved_lines': res['moved_lines'], 'total_qty': res['total_qty']})
