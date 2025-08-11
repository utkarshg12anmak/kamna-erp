from __future__ import annotations
from rest_framework import viewsets, permissions, decorators, response, status
from django.db.models import Q
from .models import State, City, Partner, GSTRegistration, Address, Contact
from .serializers import (
    StateSerializer,
    CitySerializer,
    PartnerSerializer,
    GSTRegistrationSerializer,
    AddressSerializer,
    ContactSerializer,
)


class StateViewSet(viewsets.ModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["code", "name", "country"]
    search_fields = ["code", "name", "country"]
    ordering_fields = ["code", "name"]


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.select_related("state").all()
    serializer_class = CitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["name", "state__code", "state__name"]
    search_fields = ["name", "state__code", "state__name"]
    ordering_fields = ["name", "state__name"]


class PartnerViewSet(viewsets.ModelViewSet):
    queryset = Partner.objects.all().prefetch_related("gst_regs", "addresses", "contacts")
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = [
        "status",
        "is_customer",
        "is_vendor",
        "is_carrier",
        "is_employee",
        "type",
    ]
    search_fields = ["name", "email", "phone", "gst_regs__gstin"]
    ordering_fields = ["name", "status", "type"]

    @decorators.action(detail=False, methods=["get"], url_path="quick")
    def quick(self, request):
        q = request.query_params.get("q", "").strip()
        qs = self.get_queryset()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
        data = [{"id": p.id, "name": p.name, "is_customer": p.is_customer, "is_vendor": p.is_vendor} for p in qs[:20]]
        return response.Response(data)

    @decorators.action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        p = self.get_object()
        data = {
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "type": p.type,
            "roles": {
                "customer": p.is_customer,
                "vendor": p.is_vendor,
                "carrier": p.is_carrier,
                "employee": p.is_employee,
            },
            "contacts": ContactSerializer(p.contacts.all(), many=True).data,
            "addresses": AddressSerializer(p.addresses.all(), many=True).data,
            "gst_regs": GSTRegistrationSerializer(p.gst_regs.all(), many=True).data,
        }
        return response.Response(data)


class GSTRegistrationViewSet(viewsets.ModelViewSet):
    queryset = GSTRegistration.objects.select_related("partner").all()
    serializer_class = GSTRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["gstin", "partner__id"]
    search_fields = ["gstin", "partner__name"]
    ordering_fields = ["gstin"]


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.select_related("partner", "city", "city__state").all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["type", "partner__id", "city__state__code"]
    search_fields = ["line1", "postal_code", "partner__name", "city__name"]
    ordering_fields = ["partner__name", "city__name"]


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.select_related("partner").all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["partner__id", "is_primary"]
    search_fields = ["name", "email", "phone", "partner__name"]
    ordering_fields = ["name"]
