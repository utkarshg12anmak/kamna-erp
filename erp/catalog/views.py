from django.shortcuts import render
from rest_framework import viewsets, permissions, decorators, response
from .models import Brand
from .serializers import BrandSerializer, BrandHistorySerializer

# Create your views here.

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("id")
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]

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
