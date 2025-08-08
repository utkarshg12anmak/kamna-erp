from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Brand


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
