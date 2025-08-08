from django.contrib import admin
from .models import Brand, Category, TaxRate, UoM, Item


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "active")
    search_fields = ("name",)
    list_filter = ("active",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "active")
    search_fields = ("name", "parent__name")
    list_filter = ("active",)


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "percent", "active")
    search_fields = ("name",)
    list_filter = ("active",)


@admin.register(UoM)
class UoMAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "ratio_to_base", "base", "active")
    search_fields = ("code", "name")
    list_filter = ("active", "base")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sku", "product_type", "brand", "category", "uom", "status")
    search_fields = ("name", "sku")
    list_filter = ("product_type", "status", "for_sales", "for_purchase", "for_manufacture")
