from django.shortcuts import render
from rest_framework import viewsets, permissions, decorators, response, generics, filters, status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action, api_view, permission_classes
from django.db.models import Count, Q, Sum as DjangoSum
from django.utils import timezone
from django.http import JsonResponse
from .models import Warehouse, Location, LocationType, StockLedger, AdjustmentRequest, AdjustmentStatus, WarehouseStatus
from .serializers import (
    WarehouseSerializer,
    LocationSerializer,
    WarehouseHistorySerializer,
    LocationHistorySerializer,
    StockLedgerListSerializer,
    AdjustmentRequestSerializer,
)
from .services import ensure_location_empty, request_post_moves, approve_post_moves, decline_post_moves, on_hand_qty
from .services import delete_request_revert_moves
# Add explicit imports for error translation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

# Create your views here.


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all().order_by("-updated_at")
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = ["status", "code", "city", "state"]
    search_fields = ["code", "name", "city", "state"]
    ordering_fields = ["code", "name", "updated_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @decorators.action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        wh = self.get_object()
        hist = wh.history.all().order_by("-history_date")
        data = WarehouseHistorySerializer(hist, many=True).data
        return response.Response({"results": data})

    @decorators.action(detail=True, methods=["get"], url_path="virtual_bins")
    def virtual_bins(self, request, pk=None):
        wh = self.get_object()
        bins = wh.locations.filter(type=LocationType.VIRTUAL).order_by("subtype")
        data = LocationSerializer(bins, many=True).data
        return response.Response({"results": data})

    @decorators.action(detail=False, methods=["get"], url_path="summary_by_state")
    def summary_by_state(self, request):
        qs = (
            Warehouse.objects.values("state")
            .annotate(count=Count("id"))
            .order_by("state")
        )
        data = [{"state": row["state"], "count": row["count"]} for row in qs]
        return response.Response({"results": data})

    @decorators.action(detail=True, methods=["post"], url_path="zero_return_lostpending")
    def zero_return_lostpending(self, request, pk=None):
        """Zero the RETURN and LOST_PENDING virtual bins by writing off inventory into LOST.
        Logic:
          - RETURN: move all positive on-hand to LOST (pair entries). If negative (rare), pull from LOST up to needed to zero.
          - LOST_PENDING: move all positive on-hand to LOST (finalize). Negatives ignored (should not occur).
        Uses movement_type=PUTAWAY_LOST for all postings (consistent lost semantics).
        Returns summary per bin and item counts.
        """
        from django.db import transaction
        from django.db.models import Sum
        from decimal import Decimal
        from .models import LocationType, VirtualSubtype, MovementType, StockLedger
        wh = self.get_object()
        return_bin = wh.locations.filter(type=LocationType.VIRTUAL, subtype=VirtualSubtype.RETURN).first()
        lost_pending_bin = wh.locations.filter(type=LocationType.VIRTUAL, subtype=VirtualSubtype.LOST_PENDING).first()
        lost_bin = wh.locations.filter(type=LocationType.VIRTUAL, subtype=VirtualSubtype.LOST).first()
        if not (return_bin and lost_bin):
            return response.Response({"detail": "RETURN and LOST bins required"}, status=status.HTTP_400_BAD_REQUEST)
        summary = {"return": [], "lost_pending": []}
        with transaction.atomic():
            # RETURN bin processing
            if return_bin:
                rows = (
                    StockLedger.objects.filter(warehouse=wh, location=return_bin)
                    .values("item_id")
                    .annotate(total=Sum("qty_delta"))
                )
                for r in rows:
                    qty = r["total"] or Decimal("0")
                    if qty == 0:
                        continue
                    item_id = r["item_id"]
                    if qty > 0:
                        # Move to LOST
                        StockLedger.objects.create(warehouse=wh, location=return_bin, item_id=item_id, qty_delta=-qty, movement_type=MovementType.PUTAWAY_LOST, ref_model="ZERO_BINS", ref_id="RETURN->LOST", user=request.user, memo="zero return write-off")
                        StockLedger.objects.create(warehouse=wh, location=lost_bin, item_id=item_id, qty_delta=+qty, movement_type=MovementType.PUTAWAY_LOST, ref_model="ZERO_BINS", ref_id="RETURN->LOST", user=request.user, memo="zero return write-off")
                        summary["return"].append({"item": item_id, "moved_to_lost": float(qty)})
                    else:
                        # Negative qty: attempt to pull from LOST to zero
                        need = -qty
                        lost_bal = (
                            StockLedger.objects.filter(warehouse=wh, location=lost_bin, item_id=item_id)
                            .aggregate(s=Sum("qty_delta"))
                            .get("s")
                            or Decimal("0")
                        )
                        take = min(need, lost_bal)
                        if take > 0:
                            StockLedger.objects.create(warehouse=wh, location=lost_bin, item_id=item_id, qty_delta=-take, movement_type=MovementType.PUTAWAY_LOST, ref_model="ZERO_BINS", ref_id="LOST->RETURN", user=request.user, memo="offset negative return from lost")
                            StockLedger.objects.create(warehouse=wh, location=return_bin, item_id=item_id, qty_delta=+take, movement_type=MovementType.PUTAWAY_LOST, ref_model="ZERO_BINS", ref_id="LOST->RETURN", user=request.user, memo="offset negative return from lost")
                            need -= take
                        if need > 0:
                            # Cannot fully offset; leave remainder (avoid fabricating stock)
                            summary["return"].append({"item": item_id, "unresolved_negative": float(-need)})
            # LOST_PENDING processing
            if lost_pending_bin and lost_bin:
                rows2 = (
                    StockLedger.objects.filter(warehouse=wh, location=lost_pending_bin)
                    .values("item_id")
                    .annotate(total=Sum("qty_delta"))
                )
                for r in rows2:
                    qty = r["total"] or Decimal("0")
                    if qty <= 0:
                        continue  # ignore zero/negative
                    item_id = r["item_id"]
                    StockLedger.objects.create(warehouse=wh, location=lost_pending_bin, item_id=item_id, qty_delta=-qty, movement_type=MovementType.PUTAWAY_LOST, ref_model="ZERO_BINS", ref_id="LOST_PENDING->LOST", user=request.user, memo="finalize lost pending")
                    StockLedger.objects.create(warehouse=wh, location=lost_bin, item_id=item_id, qty_delta=+qty, movement_type=MovementType.PUTAWAY_LOST, ref_model="ZERO_BINS", ref_id="LOST_PENDING->LOST", user=request.user, memo="finalize lost pending")
                    summary["lost_pending"].append({"item": item_id, "finalized": float(qty)})
        return response.Response({"ok": True, "warehouse": wh.id, "summary": summary})


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.select_related("warehouse").all().order_by("-updated_at")
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filterset_fields = {
        "warehouse": ["exact"],
        "type": ["exact"],
        "status": ["exact"],
        "code": ["icontains"],
        "subtype": ["exact"],
    }
    search_fields = ["display_name", "code"]
    ordering_fields = ["code", "display_name", "updated_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        new_status = serializer.validated_data.get("status", instance.status)
        if new_status == "INACTIVE":
            if not ensure_location_empty(instance.id):
                raise ValidationError("Inventory exists; cannot deactivate location")
        serializer.save(updated_by=self.request.user)

    @decorators.action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        loc = self.get_object()
        hist = loc.history.all().order_by("-history_date")
        data = LocationHistorySerializer(hist, many=True).data
        return response.Response({"results": data})

    @decorators.action(detail=True, methods=["post"], url_path="zero_stock")
    def zero_stock(self, request, pk=None):
        loc = self.get_object()
        # Aggregate on-hand per item at this location
        from django.db.models import Sum
        rows = (
            StockLedger.objects.filter(location=loc, warehouse=loc.warehouse)
            .values("item_id")
            .annotate(total=Sum("qty_delta"))
        )
        if not rows:
            return response.Response({"ok": True, "zeroed": 0})
        # Destination logic: positives -> move out to RETURN, negatives -> pull from RETURN (offset) or write to LOST if insuff.
        from .models import VirtualSubtype
        return_bin = loc.warehouse.locations.filter(type=LocationType.VIRTUAL, subtype=VirtualSubtype.RETURN).first()
        lost_bin = loc.warehouse.locations.filter(type=LocationType.VIRTUAL, subtype=VirtualSubtype.LOST).first()
        if not return_bin or not lost_bin:
            return response.Response({"detail": "Required virtual bins missing"}, status=status.HTTP_400_BAD_REQUEST)
        moved = []
        from .services import on_hand_qty as svc_on_hand
        for r in rows:
            qty = r["total"] or Decimal("0")
            if qty == 0:
                continue
            item_id = r["item_id"]
            if qty > 0:
                # move out qty to RETURN bin
                StockLedger.objects.create(warehouse=loc.warehouse, location=loc, item_id=item_id, qty_delta=-qty, movement_type=MovementType.TRANSFER, ref_model="LOCATION_ZERO", ref_id=str(loc.id), user=request.user, memo="zero stock out")
                StockLedger.objects.create(warehouse=loc.warehouse, location=return_bin, item_id=item_id, qty_delta=+qty, movement_type=MovementType.TRANSFER, ref_model="LOCATION_ZERO", ref_id=str(loc.id), user=request.user, memo="zero stock in RETURN")
                moved.append({"item": item_id, "delta": float(qty)})
            else:
                need = -qty
                available_return = svc_on_hand(loc.warehouse.id, return_bin.id, item_id)
                take = min(need, available_return)
                if take > 0:
                    StockLedger.objects.create(warehouse=loc.warehouse, location=return_bin, item_id=item_id, qty_delta=-take, movement_type=MovementType.TRANSFER, ref_model="LOCATION_ZERO", ref_id=str(loc.id), user=request.user, memo="offset negative via RETURN")
                    StockLedger.objects.create(warehouse=loc.warehouse, location=loc, item_id=item_id, qty_delta=+take, movement_type=MovementType.TRANSFER, ref_model="LOCATION_ZERO", ref_id=str(loc.id), user=request.user, memo="offset negative at location")
                    need -= take
                if need > 0:
                    # residual negative: post into LOST to balance
                    StockLedger.objects.create(warehouse=loc.warehouse, location=loc, item_id=item_id, qty_delta=+need, movement_type=MovementType.PUTAWAY_LOST, ref_model="LOCATION_ZERO", ref_id=str(loc.id), user=request.user, memo="cover negative with LOST")
                    StockLedger.objects.create(warehouse=loc.warehouse, location=lost_bin, item_id=item_id, qty_delta=+need, movement_type=MovementType.PUTAWAY_LOST, ref_model="LOCATION_ZERO", ref_id=str(loc.id), user=request.user, memo="from zero negative")
                    moved.append({"item": item_id, "delta": float(qty)})
        return response.Response({"ok": True, "zeroed": len(moved), "details": moved})

    @decorators.action(detail=True, methods=["post"], url_path="zero_item")
    def zero_item(self, request, pk=None):
        """Zero a single item's on-hand at this location.
        Body: {"item": <item_id>} or {"sku": "SKU"}
        Logic mirrors zero_stock but scoped to one item.
        Positive qty -> move to RETURN; negative qty -> try offset from RETURN else cover with LOST postings.
        """
        from decimal import Decimal
        from django.db import transaction
        from .models import VirtualSubtype, MovementType, StockLedger
        from catalog.models import Item
        loc = self.get_object()
        data = request.data or {}
        item_obj = None
        item_id = data.get("item")
        sku = data.get("sku")
        if item_id:
            try:
                item_obj = Item.objects.get(id=item_id)
            except Item.DoesNotExist:
                return response.Response({"detail": "Item not found"}, status=status.HTTP_400_BAD_REQUEST)
        elif sku:
            try:
                item_obj = Item.objects.get(sku=sku)
            except Item.DoesNotExist:
                return response.Response({"detail": "SKU not found"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return response.Response({"detail": "Provide item or sku"}, status=status.HTTP_400_BAD_REQUEST)
        # Compute on-hand for this item @ location
        from django.db.models import Sum
        agg = (
            StockLedger.objects.filter(warehouse=loc.warehouse, location=loc, item=item_obj)
            .aggregate(total=Sum("qty_delta"))
        )
        qty = agg["total"] or Decimal("0")
        if qty == 0:
            return response.Response({"ok": True, "zeroed": False, "before": 0, "after": 0, "detail": "Already zero"})
        return_bin = loc.warehouse.locations.filter(type=LocationType.VIRTUAL, subtype=VirtualSubtype.RETURN).first()
        lost_bin = loc.warehouse.locations.filter(type=LocationType.VIRTUAL, subtype=VirtualSubtype.LOST).first()
        if not return_bin or not lost_bin:
            return response.Response({"detail": "Required virtual bins missing"}, status=status.HTTP_400_BAD_REQUEST)
        ops = []
        from .services import on_hand_qty as svc_on_hand  # reuse existing util
        with transaction.atomic():
            if qty > 0:
                # Move out to RETURN
                StockLedger.objects.create(warehouse=loc.warehouse, location=loc, item=item_obj, qty_delta=-qty, movement_type=MovementType.TRANSFER, ref_model="LOCATION_ZERO_ITEM", ref_id=f"{loc.id}:{item_obj.id}", user=request.user, memo="zero item out")
                StockLedger.objects.create(warehouse=loc.warehouse, location=return_bin, item=item_obj, qty_delta=+qty, movement_type=MovementType.TRANSFER, ref_model="LOCATION_ZERO_ITEM", ref_id=f"{loc.id}:{item_obj.id}", user=request.user, memo="zero item to RETURN")
                ops.append({"action": "MOVE_TO_RETURN", "qty": float(qty)})
            else:
                need = -qty  # qty is negative
                available_return = svc_on_hand(loc.warehouse.id, return_bin.id, item_obj.id)
                take = min(need, available_return)
                if take > 0:
                    StockLedger.objects.create(warehouse=loc.warehouse, location=return_bin, item=item_obj, qty_delta=-take, movement_type=MovementType.TRANSFER, ref_model="LOCATION_ZERO_ITEM", ref_id=f"{loc.id}:{item_obj.id}", user=request.user, memo="offset neg via RETURN")
                    StockLedger.objects.create(warehouse=loc.warehouse, location=loc, item=item_obj, qty_delta=+take, movement_type=MovementType.TRANSFER, ref_model="LOCATION_ZERO_ITEM", ref_id=f"{loc.id}:{item_obj.id}", user=request.user, memo="offset neg at location")
                    ops.append({"action": "OFFSET_FROM_RETURN", "qty": float(take)})
                    need -= take
                if need > 0:
                    StockLedger.objects.create(warehouse=loc.warehouse, location=loc, item=item_obj, qty_delta=+need, movement_type=MovementType.PUTAWAY_LOST, ref_model="LOCATION_ZERO_ITEM", ref_id=f"{loc.id}:{item_obj.id}", user=request.user, memo="cover negative with LOST")
                    StockLedger.objects.create(warehouse=loc.warehouse, location=lost_bin, item=item_obj, qty_delta=+need, movement_type=MovementType.PUTAWAY_LOST, ref_model="LOCATION_ZERO_ITEM", ref_id=f"{loc.id}:{item_obj.id}", user=request.user, memo="zero item negative to LOST")
                    ops.append({"action": "COVER_WITH_LOST", "qty": float(need)})
        # After state
        new_qty = svc_on_hand(loc.warehouse.id, loc.id, item_obj.id)
        return response.Response({
            "ok": True,
            "zeroed": True,
            "item": item_obj.id,
            "sku": item_obj.sku,
            "before": float(qty),
            "after": float(new_qty),
            "operations": ops,
        })


# Movement log per warehouse
from rest_framework.pagination import PageNumberPagination

class MovementsPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200


class WarehouseLedgerView(generics.ListAPIView):
    serializer_class = StockLedgerListSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["item__sku", "item__name", "memo", "ref_id"]
    ordering_fields = ["ts", "qty_delta", "movement_type"]
    ordering = ["-ts"]
    pagination_class = MovementsPagination

    def get_queryset(self):
        from django.db.models import Window, F, Sum as ORM_Sum
        wh_id = self.kwargs.get("pk")
        qs = StockLedger.objects.select_related("item", "location").filter(warehouse_id=wh_id).order_by("-ts")
        # Additional filters via query params
        params = self.request.query_params
        from_loc = params.get("from_location")
        to_loc = params.get("to_location")
        mtype = params.get("type")
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        if mtype:
            qs = qs.filter(movement_type=mtype)
        if date_from:
            qs = qs.filter(ts__date__gte=date_from)
        if date_to:
            qs = qs.filter(ts__date__lte=date_to)
        if from_loc:
            # Entries that reduce stock at a specific location (e.g., transfers out, adjustments out)
            qs = qs.filter(location_id=from_loc, qty_delta__lt=0)
        if to_loc:
            # Entries that increase stock at a specific location (e.g., transfers in, adjustments in)
            qs = qs.filter(location_id=to_loc, qty_delta__gt=0)
        # Annotate per-location running total to compute before/after quantities
        running_total = Window(
            expression=ORM_Sum("qty_delta"),
            partition_by=[F("warehouse_id"), F("location_id"), F("item_id")],
            order_by=[F("ts").asc(), F("id").asc()],
        )
        qs = qs.annotate(
            location_qty_after=running_total,
            location_qty_before=running_total - F("qty_delta"),
        )
        return qs


class AdjustmentRequestPermissions(permissions.DjangoModelPermissions):
    """Require change permission for approve/decline actions; otherwise default mapping."""
    def has_permission(self, request, view):
        action = getattr(view, "action", None)
        if action in ("approve", "decline"):
            # Require change permission on the model
            try:
                opts = view.queryset.model._meta
            except Exception:
                return False
            required_perm = f"{opts.app_label}.change_{opts.model_name}"
            return request.user and request.user.is_authenticated and request.user.has_perm(required_perm)
        return super().has_permission(request, view)


class AdjustmentRequestViewSet(viewsets.ModelViewSet):
    queryset = AdjustmentRequest.objects.select_related("warehouse", "item", "source_location").all().order_by("-requested_at")
    serializer_class = AdjustmentRequestSerializer
    permission_classes = [permissions.IsAuthenticated, AdjustmentRequestPermissions]
    filterset_fields = {
        "warehouse": ["exact"],
        "type": ["exact"],
        "status": ["exact"],
        "requested_by": ["exact"],
    }
    search_fields = ["number", "item__sku", "item__name"]
    ordering_fields = ["requested_at", "number"]

    def perform_create(self, serializer):
        obj = serializer.save(requested_by=self.request.user)
        # Perform pending moves for the request
        request_post_moves(obj, self.request.user)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        if obj.status != AdjustmentStatus.REQUESTED:
            return response.Response({"detail": "Not in REQUESTED status"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            approve_post_moves(obj, request.user)
        except (DjangoValidationError, DRFValidationError) as e:
            # Normalize validation messages
            detail = getattr(e, "message", None) or getattr(e, "detail", None) or str(e)
            return response.Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Surface unexpected errors to the UI (and keep 500 semantics)
            return response.Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        obj.status = AdjustmentStatus.APPROVED
        obj.approved_by = request.user
        obj.approved_at = timezone.now()
        obj.save(update_fields=["status", "approved_by", "approved_at"])
        return response.Response(AdjustmentRequestSerializer(obj).data)

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        obj = self.get_object()
        if obj.status != AdjustmentStatus.REQUESTED:
            return response.Response({"detail": "Not in REQUESTED status"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            decline_post_moves(obj, request.user)
        except (DjangoValidationError, DRFValidationError) as e:
            detail = getattr(e, "message", None) or getattr(e, "detail", None) or str(e)
            return response.Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return response.Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        obj.status = AdjustmentStatus.DECLINED
        obj.declined_by = request.user
        obj.declined_at = timezone.now()
        obj.save(update_fields=["status", "declined_by", "declined_at"])
        return response.Response(AdjustmentRequestSerializer(obj).data)

    def perform_destroy(self, instance):
        if instance.status != AdjustmentStatus.REQUESTED:
            raise ValidationError("Only REQUESTED adjustments can be deleted")
        # Revert the request's inventory effects before deletion
        delete_request_revert_moves(instance, self.request.user)
        return super().perform_destroy(instance)


@api_view(["GET"])  # Warehouse KPIs
@permission_classes([permissions.IsAuthenticated])
def warehouse_kpis(request, pk: int):
    # Total on-hand across all items/locations (net qty)
    # Exclude LOST and EXCESS_PENDING for displayed total
    from .models import VirtualSubtype  # local import to avoid circulars at top edits
    base = StockLedger.objects.filter(warehouse_id=pk)
    excluded_subtypes = [VirtualSubtype.EXCESS_PENDING, VirtualSubtype.LOST]
    total_qty = (
        base.exclude(location__subtype__in=excluded_subtypes)
        .aggregate(total=DjangoSum("qty_delta")).get("total")
        or 0
    )
    # Distinct items with non-zero on hand (unchanged semantics)
    per_item = (
        StockLedger.objects.filter(warehouse_id=pk)
        .values("item_id")
        .annotate(q=DjangoSum("qty_delta"))
    )
    total_items = sum(1 for r in per_item if (r.get("q") or 0) != 0)
    # Locations with stock (non-zero)
    per_loc = (
        StockLedger.objects.filter(warehouse_id=pk)
        .values("location_id")
        .annotate(q=DjangoSum("qty_delta"))
    )
    locations_with_stock = sum(1 for r in per_loc if (r.get("q") or 0) != 0)
    # Movements today
    today = timezone.now().date()
    movements_today = StockLedger.objects.filter(warehouse_id=pk, ts__date=today).count()
    # LOST bin qty as a separate KPI
    lost_qty = (
        base.filter(location__subtype=VirtualSubtype.LOST)
        .aggregate(total=DjangoSum("qty_delta")).get("total")
        or 0
    )
    return response.Response({
        "total_qty": float(total_qty),
        "total_items": int(total_items),
        "locations_with_stock": int(locations_with_stock),
        "movements_today": int(movements_today),
        "lost_qty": float(lost_qty),
    })


@api_view(["GET"])  # Recent activity: last 10 movements
@permission_classes([permissions.IsAuthenticated])
def warehouse_recent_activity(request, pk: int):
    qs = (
        StockLedger.objects.select_related("item", "location")
        .filter(warehouse_id=pk)
        .order_by("-ts")[:10]
    )
    data = StockLedgerListSerializer(qs, many=True).data
    return response.Response({"results": data})


@api_view(["GET"])  # Simple on-hand endpoint
@permission_classes([permissions.IsAuthenticated])
def stock_on_hand(request):
    try:
        warehouse_id = int(request.GET.get("warehouse"))
        location_id = int(request.GET.get("location"))
        item_id = int(request.GET.get("item"))
    except (TypeError, ValueError):
        return response.Response({"detail": "warehouse, location, item are required as integers"}, status=status.HTTP_400_BAD_REQUEST)
    qty = on_hand_qty(warehouse_id, location_id, item_id)
    return response.Response({"qty": float(qty)})


@api_view(["GET"])  # Lightweight permission check for approvals UI
@permission_classes([permissions.IsAuthenticated])
def adjustment_permissions(request):
    app_label = AdjustmentRequest._meta.app_label
    model_name = AdjustmentRequest._meta.model_name
    can_change = request.user.has_perm(f"{app_label}.change_{model_name}")
    can_delete = request.user.has_perm(f"{app_label}.delete_{model_name}")
    return response.Response({"can_change": bool(can_change), "can_delete": bool(can_delete)})


@api_view(["GET"])  # Active locations stock summary and SKU breakdown
@permission_classes([permissions.IsAuthenticated])
def warehouse_active_stock_summary(request, pk: int):
    # Base filter: ACTIVE locations in this warehouse
    base_qs = StockLedger.objects.filter(warehouse_id=pk, location__status=WarehouseStatus.ACTIVE)

    # Optional subtype filter for per-row breakdown
    subtype = request.GET.get("subtype")
    if subtype:
        filtered_qs = base_qs.filter(location__subtype=subtype)
    else:
        filtered_qs = base_qs

    # Items breakdown (respecting optional subtype filter)
    qs = (
        filtered_qs
        .values("item_id", "item__sku", "item__name")
        .annotate(q=DjangoSum("qty_delta"))
    )
    items = []
    total = 0
    for r in qs:
        q = float(r.get("q") or 0)
        if q == 0:
            continue
        items.append({
            "item": int(r["item_id"]),
            "item_sku": r["item__sku"],
            "item_name": r["item__name"],
            "qty": q,
        })
        total += q

    # Per-subtype pivot across ACTIVE locations (unfiltered, for the pivot table)
    subtype_qs = (
        base_qs
        .values("location__subtype")
        .annotate(q=DjangoSum("qty_delta"))
    )
    per_subtype = []
    for r in subtype_qs:
        q = float(r.get("q") or 0)
        if q == 0:
            continue
        per_subtype.append({
            "subtype": r.get("location__subtype") or "",
            "qty": q,
        })

    return response.Response({
        "total_qty": float(total),
        "items": items,
        "grand_total": float(total),
        "per_subtype": per_subtype,
        "filter": {"subtype": subtype} if subtype else None,
    })


@api_view(["GET"])  # Physical locations stock summary and SKU breakdown
@permission_classes([permissions.IsAuthenticated])
def warehouse_physical_stock_summary(request, pk: int):
    # Base filter: ACTIVE, PHYSICAL locations in this warehouse
    base_qs = StockLedger.objects.filter(
        warehouse_id=pk,
        location__status=WarehouseStatus.ACTIVE,
        location__type=LocationType.PHYSICAL,
    )

    # Optional location filter for SKU breakdown
    loc = request.GET.get("location")
    if loc:
        try:
            loc_id = int(loc)
        except (TypeError, ValueError):
            return response.Response({"detail": "location must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
        filtered_qs = base_qs.filter(location_id=loc_id)
        qs = (
            filtered_qs
            .values("item_id", "item__sku", "item__name")
            .annotate(q=DjangoSum("qty_delta"))
        )
        items = []
        total = 0.0
        for r in qs:
            q = float(r.get("q") or 0)
            if q == 0:
                continue
            items.append({
                "item": int(r["item_id"]),
                "item_sku": r["item__sku"],
                "item_name": r["item__name"],
                "qty": q,
            })
            total += q
        return response.Response({
            "items": items,
            "grand_total": float(total),
            "filter": {"location": loc_id},
        })

    # Per-physical-location pivot and total
    pivot = (
        base_qs
        .values("location_id", "location__code", "location__display_name")
        .annotate(q=DjangoSum("qty_delta"))
    )
    per_location = []
    total_qty = 0.0
    for r in pivot:
        q = float(r.get("q") or 0)
        if q == 0:
            continue
        per_location.append({
            "location": int(r["location_id"]),
            "code": r.get("location__code") or "",
            "name": r.get("location__display_name") or "",
            "qty": q,
        })
        total_qty += q

    return response.Response({
        "total_qty": float(total_qty),
        "per_location": per_location,
    })
