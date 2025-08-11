from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StateViewSet, CityViewSet, PartnerViewSet, GSTRegistrationViewSet, AddressViewSet, ContactViewSet

router = DefaultRouter()
router.register(r"states", StateViewSet)
router.register(r"cities", CityViewSet)
router.register(r"partners", PartnerViewSet)
router.register(r"gst", GSTRegistrationViewSet)
router.register(r"addresses", AddressViewSet)
router.register(r"contacts", ContactViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
