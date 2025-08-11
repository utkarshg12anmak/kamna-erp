from __future__ import annotations
from rest_framework import serializers
from .models import State, City, Partner, GSTRegistration, Address, Contact


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "code", "name", "country"]


class CitySerializer(serializers.ModelSerializer):
    state = StateSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(source="state", queryset=State.objects.all(), write_only=True)

    class Meta:
        model = City
        fields = ["id", "name", "state", "state_id"]


class GSTRegistrationSerializer(serializers.ModelSerializer):
    partner_id = serializers.PrimaryKeyRelatedField(source="partner", queryset=Partner.objects.all(), write_only=True)

    class Meta:
        model = GSTRegistration
        fields = ["id", "gstin", "legal_name", "trade_name", "is_default", "partner", "partner_id"]
        read_only_fields = ["partner"]


class AddressSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(source="city", queryset=City.objects.all(), write_only=True)
    partner_id = serializers.PrimaryKeyRelatedField(source="partner", queryset=Partner.objects.all(), write_only=True)

    class Meta:
        model = Address
        fields = [
            "id",
            "type",
            "line1",
            "line2",
            "postal_code",
            "latitude",
            "longitude",
            "is_primary",
            "city",
            "city_id",
            "partner",
            "partner_id",
        ]
        read_only_fields = ["partner"]


class ContactSerializer(serializers.ModelSerializer):
    partner_id = serializers.PrimaryKeyRelatedField(source="partner", queryset=Partner.objects.all(), write_only=True)

    class Meta:
        model = Contact
        fields = ["id", "name", "email", "phone", "is_primary", "partner", "partner_id"]
        read_only_fields = ["partner"]


class PartnerSerializer(serializers.ModelSerializer):
    gst_regs = GSTRegistrationSerializer(many=True, required=False)
    addresses = AddressSerializer(many=True, required=False)
    contacts = ContactSerializer(many=True, required=False)

    class Meta:
        model = Partner
        fields = [
            "id",
            "name",
            "type",
            "status",
            "is_customer",
            "is_vendor",
            "is_carrier",
            "is_employee",
            "email",
            "phone",
            "gst_regs",
            "addresses",
            "contacts",
        ]

    def create(self, validated_data):
        gst_data = validated_data.pop("gst_regs", [])
        addr_data = validated_data.pop("addresses", [])
        contact_data = validated_data.pop("contacts", [])
        partner = Partner.objects.create(**validated_data)
        for g in gst_data:
            GSTRegistration.objects.create(partner=partner, **g)
        for a in addr_data:
            Address.objects.create(partner=partner, **a)
        for c in contact_data:
            Contact.objects.create(partner=partner, **c)
        return partner

    def update(self, instance, validated_data):
        gst_data = validated_data.pop("gst_regs", None)
        addr_data = validated_data.pop("addresses", None)
        contact_data = validated_data.pop("contacts", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if gst_data is not None:
            instance.gst_regs.all().delete()
            for g in gst_data:
                GSTRegistration.objects.create(partner=instance, **g)
        if addr_data is not None:
            instance.addresses.all().delete()
            for a in addr_data:
                Address.objects.create(partner=instance, **a)
        if contact_data is not None:
            instance.contacts.all().delete()
            for c in contact_data:
                Contact.objects.create(partner=instance, **c)
        return instance
