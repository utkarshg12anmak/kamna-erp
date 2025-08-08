from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Brand, Category, TaxRate, UoM, Item


class UsernameField(serializers.RelatedField):
    def to_representation(self, value):
        return getattr(value, "username", None)


class BrandSerializer(serializers.ModelSerializer):
    created_by = UsernameField(read_only=True)
    updated_by = UsernameField(read_only=True)

    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = ("created_at", "updated_at", "created_by", "updated_by")
        extra_kwargs = {
            "name": {"required": True},
        }


class BrandHistorySerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk")
    brand_id = serializers.IntegerField(source="id")
    name = serializers.CharField()
    active = serializers.BooleanField()
    history_id = serializers.IntegerField()
    history_user = serializers.SerializerMethodField()
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()

    def get_history_user(self, obj):
        user = getattr(obj, "history_user", None)
        return getattr(user, "username", None) if user else None


class CategorySerializer(serializers.ModelSerializer):
    created_by = UsernameField(read_only=True)
    updated_by = UsernameField(read_only=True)
    parent_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "parent",
            "parent_name",
            "active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = ("created_at", "updated_at", "created_by", "updated_by", "parent_name")

    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None


class CategoryHistorySerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk")
    category_id = serializers.IntegerField(source="id")
    name = serializers.CharField()
    parent = serializers.IntegerField(source="parent_id", allow_null=True)
    active = serializers.BooleanField()
    history_id = serializers.IntegerField()
    history_user = serializers.SerializerMethodField()
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()

    def get_history_user(self, obj):
        user = getattr(obj, "history_user", None)
        return getattr(user, "username", None) if user else None


class TaxRateSerializer(serializers.ModelSerializer):
    created_by = UsernameField(read_only=True)
    updated_by = UsernameField(read_only=True)

    class Meta:
        model = TaxRate
        fields = [
            "id",
            "name",
            "percent",
            "active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = ("created_at", "updated_at", "created_by", "updated_by")


class TaxRateHistorySerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk")
    taxrate_id = serializers.IntegerField(source="id")
    name = serializers.CharField()
    percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    active = serializers.BooleanField()
    history_id = serializers.IntegerField()
    history_user = serializers.SerializerMethodField()
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()

    def get_history_user(self, obj):
        user = getattr(obj, "history_user", None)
        return getattr(user, "username", None) if user else None


class UoMSerializer(serializers.ModelSerializer):
    created_by = UsernameField(read_only=True)
    updated_by = UsernameField(read_only=True)

    class Meta:
        model = UoM
        fields = [
            "id",
            "code",
            "name",
            "ratio_to_base",
            "base",
            "active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = ("created_at", "updated_at", "created_by", "updated_by")


class UoMHistorySerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk")
    uom_id = serializers.IntegerField(source="id")
    code = serializers.CharField()
    name = serializers.CharField()
    ratio_to_base = serializers.DecimalField(max_digits=10, decimal_places=4)
    base = serializers.BooleanField()
    active = serializers.BooleanField()
    history_id = serializers.IntegerField()
    history_user = serializers.SerializerMethodField()
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()

    def get_history_user(self, obj):
        user = getattr(obj, "history_user", None)
        return getattr(user, "username", None) if user else None


class ItemSerializer(serializers.ModelSerializer):
    created_by = UsernameField(read_only=True)
    updated_by = UsernameField(read_only=True)
    brand_name = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.SerializerMethodField(read_only=True)
    uom_name = serializers.SerializerMethodField(read_only=True)
    tax_rate_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Item
        fields = [
            'id','name','sku','product_type','brand','brand_name','category','category_name','uom','uom_name','tax_rate','tax_rate_name','status',
            'for_sales','for_purchase','for_manufacture','image','description','created_at','updated_at','created_by','updated_by'
        ]
        read_only_fields = ('sku','created_at','updated_at','created_by','updated_by','brand_name','category_name','uom_name','tax_rate_name')

    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_uom_name(self, obj):
        if obj.uom:
            return f"{obj.uom.code} - {obj.uom.name}"
        return None

    def get_tax_rate_name(self, obj):
        return obj.tax_rate.name if obj.tax_rate else None

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        product_type = attrs.get('product_type', getattr(instance, 'product_type', 'GOODS'))
        category = attrs.get('category', getattr(instance, 'category', None))
        uom = attrs.get('uom', getattr(instance, 'uom', None))
        status = attrs.get('status', getattr(instance, 'status', 'DRAFT'))

        # Enforce child category rules
        if product_type == 'GOODS':
            if category is None or getattr(category, 'parent_id', None) is None:
                raise serializers.ValidationError({'category': 'GOODS must have a child category (category with a parent).'})
            if uom is None:
                raise serializers.ValidationError({'uom': 'UoM is required for GOODS.'})
        else:  # SERVICE
            if category is not None and getattr(category, 'parent_id', None) is None:
                raise serializers.ValidationError({'category': 'If provided, category must be a child category.'})

        # Block edits for ARCHIVED except changing status back
        if instance is not None and instance.status == 'ARCHIVED':
            # If only status is being changed and going away from ARCHIVED allow; else block
            editable_keys = set(attrs.keys()) - {'status'}
            if editable_keys:
                raise serializers.ValidationError({'status': 'Archived items cannot be edited. Change status first.'})

        return attrs

    def create(self, validated_data):
        # SKU generated in model.save(); ensure incoming SKU ignored
        validated_data.pop('sku', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Prevent SKU changes
        if 'sku' in validated_data:
            validated_data.pop('sku')
        return super().update(instance, validated_data)


class ItemHistorySerializer(serializers.Serializer):
    history_id = serializers.IntegerField()
    history_date = serializers.DateTimeField()
    history_user = serializers.SerializerMethodField()
    history_type = serializers.CharField()
    id = serializers.IntegerField(source='pk')
    name = serializers.CharField()
    sku = serializers.CharField()
    product_type = serializers.CharField()
    brand = serializers.IntegerField(source='brand_id', allow_null=True)
    category = serializers.IntegerField(source='category_id', allow_null=True)
    uom = serializers.IntegerField(source='uom_id', allow_null=True)
    tax_rate = serializers.IntegerField(source='tax_rate_id', allow_null=True)
    status = serializers.CharField()
    for_sales = serializers.BooleanField()
    for_purchase = serializers.BooleanField()
    for_manufacture = serializers.BooleanField()

    def get_history_user(self, obj):
        user = getattr(obj, 'history_user', None)
        return getattr(user, 'username', None) if user else None
