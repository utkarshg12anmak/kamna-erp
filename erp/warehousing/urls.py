from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    WarehouseViewSet,
    LocationViewSet,
    AdjustmentRequestViewSet,
    WarehouseLedgerView,
    warehouse_kpis,
    warehouse_recent_activity,
    stock_on_hand,
    adjustment_permissions,
    warehouse_active_stock_summary,
)

router = DefaultRouter()
router.register(r"warehouses", WarehouseViewSet, basename="warehouse")
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"adjustment-requests", AdjustmentRequestViewSet, basename="adjustmentrequest")

urlpatterns = router.urls + [
    path("warehouses/<int:pk>/movements/", WarehouseLedgerView.as_view(), name="warehouse_movements"),
    path("warehouses/<int:pk>/kpis/", warehouse_kpis, name="warehouse_kpis"),
    path("warehouses/<int:pk>/recent_activity/", warehouse_recent_activity, name="warehouse_recent_activity"),
    path("warehouses/<int:pk>/active_stock_summary/", warehouse_active_stock_summary, name="warehouse_active_stock_summary"),
    path("stock_on_hand/", stock_on_hand, name="stock_on_hand"),
    path("adjustment-permissions/", adjustment_permissions, name="adjustment_permissions"),
]
