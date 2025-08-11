from rest_framework import serializers

class PutawayListRowSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    sku = serializers.CharField()
    name = serializers.CharField()
    img = serializers.CharField(allow_blank=True, required=False)
    bin_location_id = serializers.IntegerField()
    bin = serializers.CharField()
    qty = serializers.DecimalField(max_digits=12, decimal_places=3)
    last_moved_at = serializers.DateTimeField(allow_null=True)

class PutawayActionSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=[('PUTAWAY','PUTAWAY'), ('LOST','LOST')])
    item = serializers.IntegerField()
    source_bin = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=12, decimal_places=3)
    target_location = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs.get('type') == 'PUTAWAY' and not attrs.get('target_location'):
            raise serializers.ValidationError({'target_location': 'Target location is required for PUTAWAY'})
        return attrs

class PutawayBatchSerializer(serializers.Serializer):
    actions = PutawayActionSerializer(many=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)
