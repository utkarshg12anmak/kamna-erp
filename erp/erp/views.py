from django.shortcuts import render


def landing_page(request):
    return render(request, "landing_page.html")


def module_hub(request):
    return render(request, "module_hub.html")


# Helper to render module shell

def render_module(request, module, menu, content_template):
    ctx = {"module": module, "menu": menu, "content_template": content_template}
    return render(request, "base_module.html", ctx)


# Catalog module and subroutes

def catalog_menu(active_href):
    items = [
        {"label": "Dashboard", "href": "/app/catalog"},
        {"label": "Items", "href": "/app/catalog/items"},
        {"label": "Brands", "href": "/app/catalog/brands"},
        {"label": "Categories", "href": "/app/catalog/categories"},
        {"label": "UoMs", "href": "/app/catalog/uoms"},
        {"label": "Tax Rates", "href": "/app/catalog/taxrates"},
    ]
    for it in items:
        it["active"] = (it["href"] == active_href)
    return items


def module_catalog(request):
    return render_module(request, "Catalog", catalog_menu("/app/catalog"), "catalog_index.html")


def module_catalog_items(request):
    return render_module(request, "Catalog", catalog_menu("/app/catalog/items"), "catalog_items_list.html")


def module_catalog_items_new(request):
    return render_module(request, "Catalog", catalog_menu("/app/catalog/items"), "catalog_items_create.html")


def module_catalog_item_view(request, id: int):
    return render_module(request, "Catalog", catalog_menu("/app/catalog/items"), "catalog_item_view.html")


def module_catalog_item_edit(request, id: int):
    return render_module(request, "Catalog", catalog_menu("/app/catalog/items"), "catalog_items_edit.html")


def module_catalog_brands(request):
    return render_module(request, "Catalog", catalog_menu("/app/catalog/brands"), "catalog_brands.html")


def module_catalog_categories(request):
    return render_module(request, "Catalog", catalog_menu("/app/catalog/categories"), "catalog_categories.html")


def module_catalog_uoms(request):
    return render_module(request, "Catalog", catalog_menu("/app/catalog/uoms"), "catalog_uoms.html")


def module_catalog_taxrates(request):
    return render_module(request, "Catalog", catalog_menu("/app/catalog/taxrates"), "catalog_taxrates.html")


# Other modules (basic)

def module_warehousing(request):
    menu = [{"label": "Dashboard", "href": "/app/warehousing", "active": True}]
    return render_module(request, "Warehousing", menu, "warehousing_index.html")


def module_manufacturing(request):
    menu = [{"label": "Dashboard", "href": "/app/manufacturing", "active": True}]
    return render_module(request, "Manufacturing", menu, "manufacturing_index.html")


def module_sales(request):
    menu = [{"label": "Dashboard", "href": "/app/sales", "active": True}]
    return render_module(request, "Sales", menu, "sales_index.html")


def module_finance(request):
    menu = [{"label": "Dashboard", "href": "/app/finance", "active": True}]
    return render_module(request, "Finance", menu, "finance_index.html")
