from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TaxRateViewSet, UoMViewSet

router = DefaultRouter()
router.register(r"api/catalog/categories", CategoryViewSet, basename="category")
router.register(r"api/catalog/tax-rates", TaxRateViewSet, basename="taxrate")
router.register(r"api/catalog/uoms", UoMViewSet, basename="uom")

urlpatterns = []
urlpatterns += router.urls
