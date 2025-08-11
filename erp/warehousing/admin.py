from django.contrib import admin
from .models import Warehouse, Location, StockLedger, AdjustmentRequest


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "city", "state", "gstin", "updated_at")
    search_fields = ("code", "name", "city", "state", "gstin")
    list_filter = ("status", "state")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "type", "subtype", "display_name", "code", "system_managed", "status", "updated_at")
    search_fields = ("display_name", "code")
    list_filter = ("type", "status", "system_managed")


@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = ("ts", "warehouse", "location", "item", "qty_delta", "movement_type", "user")
    search_fields = ("item__sku", "item__name", "memo", "ref_id")
    list_filter = ("movement_type", "warehouse")
    date_hierarchy = "ts"


@admin.register(AdjustmentRequest)
class AdjustmentRequestAdmin(admin.ModelAdmin):
    list_display = ("number", "warehouse", "type", "item", "qty", "status", "requested_by", "requested_at")
    search_fields = ("number", "item__sku", "item__name")
    list_filter = ("type", "status", "warehouse")
