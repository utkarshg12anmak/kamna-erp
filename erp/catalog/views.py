from django.shortcuts import render
from rest_framework import viewsets, permissions, decorators, response
from .models import Brand, Category, TaxRate, UoM
from .serializers import (
    BrandSerializer,
    BrandHistorySerializer,
    CategorySerializer,
    CategoryHistorySerializer,
    TaxRateSerializer,
    TaxRateHistorySerializer,
    UoMSerializer,
    UoMHistorySerializer,
)

# Create your views here.

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("id")
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    search_fields = ["name"]

    def perform_create(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(updated_by=user)

    @decorators.action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        qs = Brand.history.filter(id=pk).order_by("-history_date")
        page = self.paginate_queryset(qs)
        serializer = BrandHistorySerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return response.Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    search_fields = ["name", "parent__name"]

    def get_queryset(self):
        qs = Category.objects.all().order_by("id")
        params = getattr(self.request, 'query_params', {})
        val = params.get("parent__isnull")
        if val is not None:
            qs = qs.filter(parent__isnull=str(val).lower() in ("1", "true", "yes"))
        act = params.get("active")
        if act is not None:
            qs = qs.filter(active=str(act).lower() in ("1", "true", "yes"))
        parent_id = params.get("parent")
        if parent_id:
            qs = qs.filter(parent_id=parent_id)
        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(updated_by=user)

    @decorators.action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        qs = Category.history.filter(id=pk).order_by("-history_date")
        page = self.paginate_queryset(qs)
        serializer = CategoryHistorySerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return response.Response(serializer.data)


class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all().order_by("id")
    serializer_class = TaxRateSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    search_fields = ["name"]

    def perform_create(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(updated_by=user)

    @decorators.action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        qs = TaxRate.history.filter(id=pk).order_by("-history_date")
        page = self.paginate_queryset(qs)
        serializer = TaxRateHistorySerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return response.Response(serializer.data)


class UoMViewSet(viewsets.ModelViewSet):
    queryset = UoM.objects.all().order_by("id")
    serializer_class = UoMSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    search_fields = ["code", "name"]

    def perform_create(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(updated_by=user)

    @decorators.action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        qs = UoM.history.filter(id=pk).order_by("-history_date")
        page = self.paginate_queryset(qs)
        serializer = UoMHistorySerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return response.Response(serializer.data)
