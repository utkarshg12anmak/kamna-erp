from django.shortcuts import render, get_object_or_404


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


# Warehousing module: separate Operational (Enter) vs Configuration menus

def warehousing_operational_menu(active_href):
    items = [
        {"label": "Dashboard", "href": "/app/warehousing"},
        {"label": "Approvals", "href": "/app/warehousing/approvals"},
    ]
    for it in items:
        it["active"] = (it["href"] == active_href)
    return items


def warehousing_config_menu(active_href):
    items = [
        {"label": "Configuration", "href": "/app/warehousing/config"},
        {"label": "Warehouses", "href": "/app/warehousing/config/warehouses"},
        {"label": "Locations", "href": "/app/warehousing/config/locations"},
    ]
    for it in items:
        it["active"] = (it["href"] == active_href)
    return items


def module_warehousing(request):
    # Operational experience (Enter)
    return render_module(request, "Warehousing", warehousing_operational_menu("/app/warehousing"), "warehousing_index.html")


def warehousing_config(request):
    return render_module(request, "Warehousing", warehousing_config_menu("/app/warehousing/config"), "warehousing_config_index.html")


def warehousing_config_warehouses(request):
    return render_module(request, "Warehousing", warehousing_config_menu("/app/warehousing/config/warehouses"), "warehousing_config_warehouses.html")


def warehousing_config_locations(request):
    return render_module(request, "Warehousing", warehousing_config_menu("/app/warehousing/config/locations"), "warehousing_config_locations.html")


# New: Operational landing page rendering state-grouped warehouses

def warehousing_enter(request):
    return render_module(request, "Warehousing", warehousing_operational_menu("/app/warehousing"), "warehousing_enter.html")


# Warehouse shell per-code

def warehouse_shell_menu(code, active_href, wh_id: int):
    base = f"/app/warehousing/w/{code}"
    items = [
        {"label": "Overview", "href": base},
        {"label": "Movements", "href": base + "/movements"},
        {"label": "Putaway", "href": base + "/putaway"},
        {"label": "Internal Movement", "href": base + "/internal-move"},
        {"label": "Approvals", "href": base + "/approvals"},
        {"label": "Adjust", "href": base + "/adjust"},
    ]
    for it in items:
        it["active"] = (it["href"] == active_href)
    return items


def warehouse_shell(request, code: str):
    from warehousing.models import Warehouse
    wh = get_object_or_404(Warehouse, code=code)
    ctx_extra = {
        "warehouse": {
            "id": wh.id,
            "code": wh.code,
            "name": wh.name,
            "status": wh.status,
            "city": wh.city,
            "state": wh.state,
            "gstin": wh.gstin,
        }
    }
    resp = render(request, "base_module.html", {
        "module": "Warehousing",
        "menu": warehouse_shell_menu(code, f"/app/warehousing/w/{code}", wh.id),
        "content_template": "warehouse_overview.html",
        **ctx_extra,
    })
    return resp


def warehouse_movements(request, code: str):
    from warehousing.models import Warehouse
    wh = get_object_or_404(Warehouse, code=code)
    ctx_extra = {
        "warehouse": {
            "id": wh.id,
            "code": wh.code,
            "name": wh.name,
        }
    }
    return render(request, "base_module.html", {
        "module": "Warehousing",
        "menu": warehouse_shell_menu(code, f"/app/warehousing/w/{code}/movements", wh.id),
        "content_template": "warehouse_movements.html",
        **ctx_extra,
    })


def warehouse_adjust(request, code: str):
    from warehousing.models import Warehouse
    wh = get_object_or_404(Warehouse, code=code)
    ctx_extra = {
        "warehouse": {
            "id": wh.id,
            "code": wh.code,
            "name": wh.name,
        }
    }
    return render(request, "base_module.html", {
        "module": "Warehousing",
        "menu": warehouse_shell_menu(code, f"/app/warehousing/w/{code}/adjust", wh.id),
        "content_template": "warehouse_adjust.html",
        **ctx_extra,
    })


# New: Approvals pages (global and per-warehouse)

def warehousing_approvals(request):
    # Global approvals list
    return render_module(request, "Warehousing", warehousing_operational_menu("/app/warehousing/approvals"), "warehousing_approvals.html")


def warehouse_approvals(request, code: str):
    from warehousing.models import Warehouse
    wh = get_object_or_404(Warehouse, code=code)
    ctx_extra = {
        "warehouse": {
            "id": wh.id,
            "code": wh.code,
            "name": wh.name,
        }
    }
    return render(request, "base_module.html", {
        "module": "Warehousing",
        "menu": warehouse_shell_menu(code, f"/app/warehousing/w/{code}/approvals", wh.id),
        "content_template": "warehouse_approvals.html",
        **ctx_extra,
    })


def warehouse_putaway(request, code: str):
    from warehousing.models import Warehouse
    wh = get_object_or_404(Warehouse, code=code)
    ctx_extra = {
        "warehouse": {
            "id": wh.id,
            "code": wh.code,
            "name": wh.name,
        }
    }
    return render(request, "base_module.html", {
        "module": "Warehousing",
        "menu": warehouse_shell_menu(code, f"/app/warehousing/w/{code}/putaway", wh.id),
        "content_template": "warehouse_putaway.html",
        **ctx_extra,
    })


def warehouse_internal_move(request, code: str):
    from warehousing.models import Warehouse
    wh = get_object_or_404(Warehouse, code=code)
    ctx_extra = {
        "warehouse": {"id": wh.id, "code": wh.code, "name": wh.name}
    }
    return render(request, "base_module.html", {
        "module": "Warehousing",
        "menu": warehouse_shell_menu(code, f"/app/warehousing/w/{code}/internal-move", wh.id),
        "content_template": "warehouse_internal_move.html",
        **ctx_extra,
    })


def warehouse_internal_move_rows(request, code: str):
    from warehousing.models import Warehouse
    wh = get_object_or_404(Warehouse, code=code)
    ctx_extra = {
        "warehouse_id": wh.id,
        "warehouse_code": wh.code,
        "warehouse": {"id": wh.id, "code": wh.code, "name": wh.name},
    }
    return render(request, "base_module.html", {
        "module": "Warehousing",
        "menu": warehouse_shell_menu(code, f"/app/warehousing/w/{code}/internal-move", wh.id),
        "content_template": "warehouse_internal_move_rows.html",
        **ctx_extra,
    })


# Other modules (basic)

def module_manufacturing(request):
    menu = [{"label": "Dashboard", "href": "/app/manufacturing", "active": True}]
    return render_module(request, "Manufacturing", menu, "manufacturing_index.html")


def module_sales(request):
    menu = [{"label": "Dashboard", "href": "/app/sales", "active": True}]
    return render_module(request, "Sales", menu, "sales_index.html")


def module_finance(request):
    menu = [{"label": "Dashboard", "href": "/app/finance", "active": True}]
    return render_module(request, "Finance", menu, "finance_index.html")


# CV Hub module

def cv_hub_menu(active_href):
    items = [
        {"label": "Dashboard", "href": "/app/cv_hub"},
        {"label": "Entries", "href": "/app/cv_hub/entries"},
        {"label": "Quick Create", "href": "/app/cv_hub/entries/new", "modal": True},
    ]
    for it in items:
        it["active"] = (it["href"] == active_href)
    return items


def module_cv_hub(request):
    return render_module(request, "Customer & Vendor Hub", cv_hub_menu("/app/cv_hub"), "cv_hub/cv_hub_index.html")


def cv_hub_entries(request):
    return render_module(request, "Customer & Vendor Hub", cv_hub_menu("/app/cv_hub/entries"), "cv_hub/cv_hub_list.html")


def cv_hub_entries_new(request):
    return render_module(request, "Customer & Vendor Hub", cv_hub_menu("/app/cv_hub/entries"), "cv_hub/cv_hub_list.html")


def cv_hub_entry_view(request, id: int):
    return render_module(request, "Customer & Vendor Hub", cv_hub_menu("/app/cv_hub/entries"), "cv_hub/cv_hub_view.html")


def cv_hub_entry_edit(request, id: int):
    return render_module(request, "Customer & Vendor Hub", cv_hub_menu("/app/cv_hub/entries"), "cv_hub/cv_hub_form.html")
