from django.shortcuts import render
from rest_framework import viewsets, permissions, decorators, response, parsers
from .models import Brand, Category, TaxRate, UoM, Item
from .serializers import (
    BrandSerializer,
    BrandHistorySerializer,
    CategorySerializer,
    CategoryHistorySerializer,
    TaxRateSerializer,
    TaxRateHistorySerializer,
    UoMSerializer,
    UoMHistorySerializer,
    ItemSerializer,
    ItemHistorySerializer,
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


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.select_related('brand','category','uom','tax_rate').all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    search_fields = ['name','sku']
    ordering_fields = ['name','updated_at','sku']
    filterset_fields = ['brand','category','status','for_sales','for_purchase','for_manufacture','product_type']

    def get_queryset(self):
        qs = Item.objects.select_related('brand','category','uom','tax_rate').all()
        params = getattr(self.request, 'query_params', {})
        # Filter exact fields
        for f in ['brand','category','status','for_sales','for_purchase','for_manufacture','product_type']:
            if f in params:
                val = params.get(f)
                if f in ['for_sales','for_purchase','for_manufacture']:
                    qs = qs.filter(**{f: str(val).lower() in ('1','true','yes')})
                else:
                    qs = qs.filter(**{f: val})
        # Default ordering by name
        return qs.order_by('name')

    def perform_create(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request and self.request.user.is_authenticated else None
        serializer.save(updated_by=user)

    @decorators.action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        qs = Item.history.filter(id=pk).order_by('-history_date')
        page = self.paginate_queryset(qs)
        serializer = ItemHistorySerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return response.Response(serializer.data)

    @decorators.action(detail=True, methods=['post'], url_path='image', parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def upload_image(self, request, pk=None):
        obj = self.get_object()
        image = request.FILES.get('image')
        if not image:
            return response.Response({'detail': 'No image provided'}, status=400)
        obj.image = image
        obj.save()
        return response.Response(ItemSerializer(obj, context=self.get_serializer_context()).data)
