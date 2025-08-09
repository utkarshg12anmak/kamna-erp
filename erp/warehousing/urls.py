from rest_framework.routers import DefaultRouter
from .views import WarehouseViewSet, LocationViewSet

router = DefaultRouter()
router.register(r"warehouses", WarehouseViewSet, basename="warehouse")
router.register(r"locations", LocationViewSet, basename="location")

urlpatterns = router.urls
