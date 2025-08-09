from django.contrib import admin
from .models import Warehouse, Location


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
