from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Warehouse, Location, LocationType, VirtualSubtype, PhysicalSubtype, WarehouseStatus

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
