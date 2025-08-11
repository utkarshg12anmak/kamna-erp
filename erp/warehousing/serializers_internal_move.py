from rest_framework import serializers
from decimal import Decimal

class StockRowSerializer(serializers.Serializer):
    item = serializers.IntegerField()
    item_sku = serializers.CharField()
    item_name = serializers.CharField()
    location = serializers.IntegerField()
    location_code = serializers.CharField(required=False, allow_blank=True)
    location_name = serializers.CharField(required=False, allow_blank=True)
    qty = serializers.DecimalField(max_digits=12, decimal_places=3)

class InternalMoveLineSerializer(serializers.Serializer):
    item = serializers.IntegerField()
    source_location = serializers.IntegerField()
    target_location = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=12, decimal_places=3)

    def validate_qty(self, v):
        if v is None or Decimal(v) <= 0:
            raise serializers.ValidationError("Quantity must be > 0")
        return v

class InternalMovePayloadSerializer(serializers.Serializer):
    lines = InternalMoveLineSerializer(many=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

# Row-form serializers
class FromStockRowSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    sku = serializers.CharField()
    name = serializers.CharField()
    img = serializers.CharField(allow_null=True)
    on_hand = serializers.DecimalField(max_digits=12, decimal_places=3)

class RowLineSerializer(serializers.Serializer):
    item = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=12, decimal_places=3)

class RowMovePayloadSerializer(serializers.Serializer):
    from_location = serializers.IntegerField()
    to_location = serializers.IntegerField()
    memo = serializers.CharField(required=False, allow_blank=True)
    lines = RowLineSerializer(many=True)
