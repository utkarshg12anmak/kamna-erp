from rest_framework import serializers
from ..models import STN, STNDetail, STNStatusHistory
from ..utils import get_available_physical_qty
from .errors import SKU_DUPLICATE, QTY_EXCEEDS_AVAILABLE, WAREHOUSES_SAME


class STNDetailSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source='sku.sku', read_only=True)
    sku_name = serializers.CharField(source='sku.name', read_only=True)
    sku_thumb = serializers.ImageField(source='sku.thumbnail', read_only=True)
    available_physical_qty = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = STNDetail
        fields = ['id', 'stn', 'sku', 'sku_code', 'sku_name', 'sku_thumb', 'created_qty', 'available_physical_qty']
        read_only_fields = ['stn']

    def get_available_physical_qty(self, obj):
        return get_available_physical_qty(obj.sku_id, obj.stn.source_warehouse_id)

    def validate(self, attrs):
        stn = self.context.get('stn') or self.instance.stn
        sku = attrs.get('sku') or (self.instance.sku if self.instance else None)
        created_qty = attrs.get('created_qty')
        
        if created_qty is not None and sku:
            # Check for duplicate SKU
            existing_qs = STNDetail.objects.filter(stn=stn, sku=sku)
            if self.instance:
                existing_qs = existing_qs.exclude(id=self.instance.id)
            
            if existing_qs.exists():
                raise serializers.ValidationError({
                    'sku': {
                        'code': SKU_DUPLICATE,
                        'detail': 'SKU already present in this STN'
                    }
                })
            
            # Check quantity > 0
            if created_qty <= 0:
                raise serializers.ValidationError({
                    'created_qty': 'Quantity must be greater than 0'
                })
            
            # Check against available quantity
            available = get_available_physical_qty(sku.id, stn.source_warehouse_id)
            if created_qty > available:
                raise serializers.ValidationError({
                    'created_qty': {
                        'code': QTY_EXCEEDS_AVAILABLE,
                        'detail': f'Max {available}'
                    }
                })
        
        return attrs


class STNSerializer(serializers.ModelSerializer):
    lines = STNDetailSerializer(many=True, read_only=True)

    class Meta:
        model = STN
        fields = [
            'id', 'stn_code', 'source_warehouse', 'destination_warehouse', 'status', 'notes',
            'sum_created_qty', 'sum_dispatched_qty', 'sum_received_qty',
            'created_at', 'updated_at', 'created_by', 'updated_by', 'lines'
        ]
        read_only_fields = [
            'stn_code', 'status', 'sum_created_qty', 'sum_dispatched_qty', 'sum_received_qty',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]

    def validate(self, attrs):
        source_warehouse = attrs.get('source_warehouse') or (self.instance.source_warehouse if self.instance else None)
        destination_warehouse = attrs.get('destination_warehouse') or (self.instance.destination_warehouse if self.instance else None)
        
        if source_warehouse and destination_warehouse and source_warehouse.id == destination_warehouse.id:
            raise serializers.ValidationError({
                'destination_warehouse': {
                    'code': WAREHOUSES_SAME,
                    'detail': 'Source and destination warehouse cannot be same'
                }
            })
        
        return attrs


class STNStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)

    class Meta:
        model = STNStatusHistory
        fields = ['id', 'from_status', 'to_status', 'reason', 'changed_by', 'changed_by_name', 'changed_at']
