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


class WarehouseHistorySerializer(serializers.ModelSerializer):
    history_user = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse.history.model
        fields = [
            "history_date",
            "history_type",
            "history_user",
            "code",
            "name",
            "status",
        ]

    def get_history_user(self, obj):
        return getattr(obj.history_user, "username", None)


class LocationSerializer(serializers.ModelSerializer):
    created_by = UsernameField()
    updated_by = UsernameField()
    warehouse_display = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            "id",
            "warehouse",
            "warehouse_display",
            "type",
            "subtype",
            "display_name",
            "code",
            "system_managed",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = ["system_managed", "created_at", "updated_at", "created_by", "updated_by", "warehouse_display"]

    def get_warehouse_display(self, obj):
        if obj.warehouse_id and getattr(obj, "warehouse", None):
            return f"{obj.warehouse.code} — {obj.warehouse.name}"
        return None

    def validate(self, attrs):
        loc_type = attrs.get("type", getattr(self.instance, "type", None))
        system_managed = attrs.get("system_managed", getattr(self.instance, "system_managed", False))
        display_name = attrs.get("display_name", getattr(self.instance, "display_name", ""))
        code = attrs.get("code", getattr(self.instance, "code", ""))
        subtype = attrs.get("subtype", getattr(self.instance, "subtype", None))
        warehouse = attrs.get("warehouse", getattr(self.instance, "warehouse", None))

        if loc_type == LocationType.PHYSICAL:
            if not display_name:
                raise serializers.ValidationError({"display_name": "Display name is required for PHYSICAL locations"})
            if not code:
                raise serializers.ValidationError({"code": "Code is required for PHYSICAL locations"})
            # Default to STORAGE and enforce
            if not subtype:
                attrs["subtype"] = PhysicalSubtype.STORAGE
            elif subtype != PhysicalSubtype.STORAGE:
                raise serializers.ValidationError({"subtype": "PHYSICAL locations must have subtype STORAGE"})
        elif loc_type == LocationType.VIRTUAL:
            if not subtype:
                raise serializers.ValidationError({"subtype": "Subtype is required for VIRTUAL locations"})
            if subtype == PhysicalSubtype.STORAGE:
                raise serializers.ValidationError({"subtype": "VIRTUAL locations cannot use STORAGE subtype"})
        else:
            raise serializers.ValidationError({"type": "Invalid location type"})

        if self.instance and system_managed:
            orig = self.instance
            if (orig.code != code) or (orig.display_name != display_name) or (orig.subtype != attrs.get("subtype", subtype)):
                raise serializers.ValidationError("System-managed locations cannot be renamed")

        # Unique code per warehouse for PHYSICAL
        if loc_type == LocationType.PHYSICAL and warehouse and code:
            qs = Location.objects.filter(warehouse=warehouse, code__iexact=code, type=LocationType.PHYSICAL)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"code": "Code must be unique per warehouse"})

        return attrs


class LocationHistorySerializer(serializers.ModelSerializer):
    history_user = serializers.SerializerMethodField()

    class Meta:
        model = Location.history.model
        fields = [
            "history_date",
            "history_type",
            "history_user",
            "type",
            "subtype",
            "display_name",
            "code",
            "status",
        ]

    def get_history_user(self, obj):
        return getattr(obj.history_user, "username", None)


# Movement log list serializer
class StockLedgerListSerializer(serializers.ModelSerializer):
    item_sku = serializers.CharField(source="item.sku", read_only=True)
    item_name = serializers.CharField(source="item.name", read_only=True)
    user = UsernameField(source="user")
    # New: human-friendly location fields
    location_name = serializers.CharField(source="location.display_name", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)
    location_subtype = serializers.CharField(source="location.subtype", read_only=True)

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
