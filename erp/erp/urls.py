"""
URL configuration for erp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from catalog.views import BrandViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    landing_page,
    module_hub,
    module_catalog,
    module_warehousing,
    module_manufacturing,
    module_sales,
    module_finance,
    module_catalog_items,
    module_catalog_items_new,
    module_catalog_item_view,
    module_catalog_item_edit,
    module_catalog_brands,
    module_catalog_categories,
    module_catalog_uoms,
    module_catalog_taxrates,
    warehousing_config,
    warehousing_config_warehouses,
    warehousing_config_locations,
    warehousing_enter,
    warehouse_shell,
    warehouse_movements,
    warehouse_adjust,
    warehousing_approvals,
    warehouse_approvals,
    warehouse_putaway,
    warehouse_internal_move,
    warehouse_internal_move_rows,
)
from .api_auth_views import AuthMeView
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r"api/catalog/brands", BrandViewSet, basename="brand")

urlpatterns = [
    path("", landing_page, name="landing_page"),
    path("admin/", admin.site.urls),
    path("", include(router.urls)),
    path("", include("catalog.urls")),
    path("api/warehousing/", include("warehousing.urls")),
    path("api/auth/jwt/create/", TokenObtainPairView.as_view(), name="jwt-create"),
    path("api/auth/jwt/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
    path("api/auth/me/", AuthMeView.as_view(), name="auth-me"),
    path("app", module_hub, name="module_hub"),
    path("app/", module_hub, name="module_hub_slash"),
    path("app/catalog", module_catalog, name="module_catalog"),
    path("app/catalog/items", module_catalog_items, name="module_catalog_items"),
    path("app/catalog/items/new", module_catalog_items_new, name="module_catalog_items_new"),
    path("app/catalog/items/<int:id>", module_catalog_item_view, name="module_catalog_item_view"),
    path("app/catalog/items/<int:id>/edit", module_catalog_item_edit, name="module_catalog_item_edit"),
    path("app/catalog/brands", module_catalog_brands, name="module_catalog_brands"),
    path("app/catalog/categories", module_catalog_categories, name="module_catalog_categories"),
    path("app/catalog/uoms", module_catalog_uoms, name="module_catalog_uoms"),
    path("app/catalog/taxrates", module_catalog_taxrates, name="module_catalog_taxrates"),
    path("app/warehousing", warehousing_enter, name="warehousing_enter"),
    path("app/warehousing/w/<str:code>", warehouse_shell, name="warehouse_shell"),
    path("app/warehousing/w/<str:code>/movements", warehouse_movements, name="warehouse_movements"),
    path("app/warehousing/w/<str:code>/putaway", warehouse_putaway, name="warehouse_putaway"),
    path("app/warehousing/w/<str:code>/adjust", warehouse_adjust, name="warehouse_adjust"),
    path("app/warehousing/approvals", warehousing_approvals, name="warehousing_approvals"),
    path("app/warehousing/w/<str:code>/approvals", warehouse_approvals, name="warehouse_approvals"),
    # Warehousing configuration routes
    path("app/warehousing/config", warehousing_config, name="warehousing_config"),
    path("app/warehousing/config/warehouses", warehousing_config_warehouses, name="warehousing_config_warehouses"),
    path("app/warehousing/config/locations", warehousing_config_locations, name="warehousing_config_locations"),
    path("app/manufacturing", module_manufacturing, name="module_manufacturing"),
    path("app/sales", module_sales, name="module_sales"),
    path("app/finance", module_finance, name="module_finance"),
    path("app/warehousing/w/<str:code>/internal-move", warehouse_internal_move_rows, name="warehouse_internal_move_rows"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
