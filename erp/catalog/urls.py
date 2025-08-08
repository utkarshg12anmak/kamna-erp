from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TaxRateViewSet, UoMViewSet, ItemViewSet

router = DefaultRouter()
router.register(r"api/catalog/categories", CategoryViewSet, basename="category")
router.register(r"api/catalog/tax-rates", TaxRateViewSet, basename="taxrate")
router.register(r"api/catalog/uoms", UoMViewSet, basename="uom")
router.register(r"api/catalog/items", ItemViewSet, basename="item")

urlpatterns = []
urlpatterns += router.urls
