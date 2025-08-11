from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Warehouse,
    Location,
    LocationType,
    VirtualSubtype,
    PhysicalSubtype,
    WarehouseStatus,
    StockLedger,
    AdjustmentRequest,
)

User = get_user_model()


class UsernameField(serializers.ReadOnlyField):
    def to_representation(self, value):
        return getattr(value, "username", None)


class WarehouseSerializer(serializers.ModelSerializer):
    created_by = UsernameField()
    updated_by = UsernameField()

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "warehouse_id",
            "code",
            "name",
            "status",
            "gstin",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "pincode",
            "country",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = ["warehouse_id", "created_at", "updated_at", "created_by", "updated_by"]

    def validate_gstin(self, v):
        import re
        if not re.match(r"^[0-9A-Z]{15}$", v or ""):
            raise serializers.ValidationError("Invalid GSTIN; must be 15 chars (A-Z, 0-9)")
        return v

    def validate(self, attrs):
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        if lat is not None and not (-90 <= float(lat) <= 90):
            raise serializers.ValidationError({"latitude": "Latitude must be between -90 and 90"})
        if lon is not None and not (-180 <= float(lon) <= 180):
            raise serializers.ValidationError({"longitude": "Longitude must be between -180 and 180"})
        return attrs


class LocationSerializer(serializers.ModelSerializer):
    created_by = UsernameField()
    updated_by = UsernameField()

    class Meta:
        model = Location
        fields = [
            "id",
            "warehouse",
            "code",
            "display_name",
            "type",
            "subtype",
            "system_managed",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = ["system_managed", "created_at", "updated_at", "created_by", "updated_by"]


class LocationHistorySerializer(serializers.ModelSerializer):
    history_user = serializers.SerializerMethodField()

    class Meta:
        model = Location.history.model
        fields = [
            "id",
            "warehouse",
            "code",
            "display_name",
            "type",
            "subtype",
            "system_managed",
            "status",
            "history_id",
            "history_date",
            "history_type",
            "history_user",
        ]

    def get_history_user(self, obj):
        return getattr(obj.history_user, "username", None)


class WarehouseHistorySerializer(serializers.ModelSerializer):
    history_user = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse.history.model
        fields = [
            "id",
            "warehouse_id",
            "code",
            "name",
            "status",
            "gstin",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "pincode",
            "country",
            "latitude",
            "longitude",
            "history_id",
            "history_date",
            "history_type",
            "history_user",
        ]

    def get_history_user(self, obj):
        return getattr(obj.history_user, "username", None)


# Movement log list serializer
class StockLedgerListSerializer(serializers.ModelSerializer):
    item_sku = serializers.CharField(source="item.sku", read_only=True)
    item_name = serializers.CharField(source="item.name", read_only=True)
    user = UsernameField()
    # New: human-friendly location fields
    location_name = serializers.CharField(source="location.display_name", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)
    location_subtype = serializers.CharField(source="location.subtype", read_only=True)
    # New: before/after quantities at the movement's location
    location_qty_before = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)
    location_qty_after = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)

    class Meta:
        model = StockLedger
        fields = [
            "id",
            "ts",
            "warehouse",
            "location",
            "location_name",
            "location_code",
            "location_subtype",
            "item",
            "item_sku",
            "item_name",
            "qty_delta",
            "movement_type",
            "ref_model",
            "ref_id",
            "memo",
            "user",
            "location_qty_before",
            "location_qty_after",
        ]
        read_only_fields = fields


class AdjustmentRequestSerializer(serializers.ModelSerializer):
    requested_by = UsernameField()
    approved_by = UsernameField()
    declined_by = UsernameField()
    # Extra display fields for UI convenience
    item_sku = serializers.CharField(source="item.sku", read_only=True)
    item_name = serializers.CharField(source="item.name", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    source_location_name = serializers.CharField(source="source_location.display_name", read_only=True)
    source_location_code = serializers.CharField(source="source_location.code", read_only=True)

    class Meta:
        model = AdjustmentRequest
        fields = [
            "id",
            "number",
            "warehouse",
            "warehouse_code",
            "warehouse_name",
            "type",
            "item",
            "item_sku",
            "item_name",
            "source_location",
            "source_location_name",
            "source_location_code",
            "qty",
            "status",
            "memo",
            "requested_by",
            "requested_at",
            "approved_by",
            "approved_at",
            "declined_by",
            "declined_at",
        ]
        read_only_fields = [
            "number",
            "status",
            "requested_by",
            "requested_at",
            "approved_by",
            "approved_at",
            "declined_by",
            "declined_at",
            "warehouse_code",
            "warehouse_name",
            "item_sku",
            "item_name",
            "source_location_name",
            "source_location_code",
        ]

    def validate_qty(self, v):
        # Must be a positive integer
        if v is None or v <= 0:
            raise serializers.ValidationError("Quantity must be > 0")
        try:
            from decimal import Decimal
            if Decimal(v) != Decimal(v).to_integral_value():
                raise serializers.ValidationError("Quantity must be a positive integer")
        except Exception:
            raise serializers.ValidationError("Quantity must be a positive integer")
        return v

# No serializer changes required; StockLedgerListSerializer already includes movement_type and user.
