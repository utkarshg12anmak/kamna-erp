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
        return super().perform_destroy(instance)


@api_view(["GET"])  # Warehouse KPIs
@permission_classes([permissions.IsAuthenticated])
def warehouse_kpis(request, pk: int):
    # Total on-hand across all items/locations (net qty)
    total_qty = (
        StockLedger.objects.filter(warehouse_id=pk).aggregate(total=DjangoSum("qty_delta")).get("total")
        or 0
    )
    # Distinct items with non-zero on hand
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
    return response.Response({
        "total_qty": float(total_qty),
        "total_items": int(total_items),
        "locations_with_stock": int(locations_with_stock),
        "movements_today": int(movements_today),
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
    return response.Response({"can_change": bool(can_change)})


@api_view(["GET"])  # Active locations stock summary and SKU breakdown
@permission_classes([permissions.IsAuthenticated])
def warehouse_active_stock_summary(request, pk: int):
    # Aggregate stock on-hand limited to ACTIVE locations
    qs = (
        StockLedger.objects
        .filter(warehouse_id=pk, location__status=WarehouseStatus.ACTIVE)
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
    return response.Response({
        "total_qty": float(total),
        "items": items,
        "grand_total": float(total),
    })
