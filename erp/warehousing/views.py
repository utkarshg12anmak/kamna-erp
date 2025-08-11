from django.shortcuts import render
from rest_framework import viewsets, permissions, decorators, response
from rest_framework.exceptions import ValidationError
from django.db.models import Count
from .models import Warehouse, Location, LocationType
from .serializers import (
    WarehouseSerializer,
    LocationSerializer,
    WarehouseHistorySerializer,
    LocationHistorySerializer,
)
from .services import ensure_location_empty

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
