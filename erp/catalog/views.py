from django.shortcuts import render
from rest_framework import viewsets
from .models import Brand
from .serializers import BrandSerializer

# Create your views here.

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("id")
    serializer_class = BrandSerializer
