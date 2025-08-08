from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Brand, Category, TaxRate, UoM


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
