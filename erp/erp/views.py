from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse


def landing_page(request):
    return render(request, "landing_page.html")


def user_mapping_debug(request):
    debug_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Mapping Debug</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container mt-4">
        <h1>User Mapping Debug Tool</h1>
        <div class="alert alert-info">
            <strong>Debug Status:</strong> Testing user assignment buttons functionality
            <br><strong>User:</strong> """ + (f"{request.user.username} (authenticated)" if request.user.is_authenticated else "Anonymous (not authenticated)") + """
        </div>
        
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Debug Output</h5>
                    </div>
                    <div class="card-body">
                        <div id="debugOutput" class="bg-light p-3" style="font-family: monospace; white-space: pre-wrap; height: 400px; overflow-y: auto;"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>API Tests</h5>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-primary mb-2 w-100" onclick="testEmployeesAPI()">Test Employees API</button>
                        <button class="btn btn-info mb-2 w-100" onclick="testAvailableUsersAPI()">Test Available Users API</button>
                        <button class="btn btn-warning mb-2 w-100" onclick="testAssignmentAPI()">Test Assignment API</button>
                        <button class="btn btn-secondary mb-2 w-100" onclick="clearDebug()">Clear Debug</button>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Direct Page Test</h5>
                    </div>
                    <div class="card-body">
                        """ + ('''
                        <button class="btn btn-success mb-2 w-100" onclick="goToEmployeesPage()">Go to Employees Page</button>
                        <button class="btn btn-outline-primary mb-2 w-100" onclick="testJavaScriptInEmployeePage()">Test JS Functions</button>
                        ''' if request.user.is_authenticated else '''
                        <div class="alert alert-warning">
                            <strong>Authentication Required:</strong><br>
                            <a href="/admin/login/?next=/debug/user-mapping" class="btn btn-primary btn-sm">Login via Admin</a><br>
                            <small>Use: test / test123</small>
                        </div>
                        ''') + """
                        <button class="btn btn-outline-info mb-2 w-100" onclick="checkBrowserConsole()">Check Browser Console</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function log(message, type = 'info') {
            const debugOutput = document.getElementById('debugOutput');
            const timestamp = new Date().toLocaleTimeString();
            const typeIcon = {
                'info': 'ℹ️',
                'success': '✅',
                'error': '❌',
                'warning': '⚠️'
            };
            
            debugOutput.textContent += `[${timestamp}] ${typeIcon[type] || 'ℹ️'} ${message}\\n`;
            debugOutput.scrollTop = debugOutput.scrollHeight;
        }
        
        function clearDebug() {
            document.getElementById('debugOutput').textContent = '';
        }
        
        async function testEmployeesAPI() {
            log('Testing Employees API...');
            try {
                const response = await fetch('/api/hr/employees/', {
                    credentials: 'same-origin'
                });
                log(`Response status: ${response.status} ${response.statusText}`);
                
                if (response.ok) {
                    const data = await response.json();
                    const employees = data.results || data;
                    log(`Success! Found ${employees.length} employees`, 'success');
                    if (employees.length > 0) {
                        log(`First employee: ${employees[0].first_name} ${employees[0].last_name} (ID: ${employees[0].id})`);
                        log(`User mapping: ${employees[0].user_username ? 'Has user: ' + employees[0].user_username : 'No user assigned'}`);
                    }
                } else {
                    const errorText = await response.text();
                    log(`Error: ${errorText}`, 'error');
                }
            } catch (error) {
                log(`Network error: ${error.message}`, 'error');
            }
        }
        
        async function testAvailableUsersAPI() {
            log('Testing Available Users API...');
            try {
                const response = await fetch('/api/hr/available-users/', {
                    credentials: 'same-origin'
                });
                log(`Response status: ${response.status} ${response.statusText}`);
                
                if (response.ok) {
                    const data = await response.json();
                    log(`Success! Found ${data.length} available users`, 'success');
                    data.forEach(user => {
                        log(`  - ${user.username} (${user.first_name} ${user.last_name}) - ${user.email}`);
                    });
                } else {
                    const errorText = await response.text();
                    log(`Error: ${errorText}`, 'error');
                    if (response.status === 403) {
                        log('Authentication required - this is normal', 'warning');
                    }
                }
            } catch (error) {
                log(`Network error: ${error.message}`, 'error');
            }
        }
        
        async function testAssignmentAPI() {
            log('Testing assignment workflow...');
            
            // First get employees
            const employeesResponse = await fetch('/api/hr/employees/', {
                credentials: 'same-origin'
            });
            
            if (!employeesResponse.ok) {
                log('Cannot get employees list', 'error');
                return;
            }
            
            const employeesData = await employeesResponse.json();
            const employees = employeesData.results || employeesData;
            
            if (employees.length === 0) {
                log('No employees found', 'warning');
                return;
            }
            
            const unassignedEmployee = employees.find(emp => !emp.user_username);
            if (!unassignedEmployee) {
                log('All employees have users assigned', 'warning');
                return;
            }
            
            log(`Found unassigned employee: ${unassignedEmployee.first_name} ${unassignedEmployee.last_name} (ID: ${unassignedEmployee.id})`);
            
            // Test the assign user endpoint
            const csrfToken = getCookie('csrftoken');
            log(`CSRF Token: ${csrfToken ? 'Found' : 'Missing'}`);
            
            if (!csrfToken) {
                log('CSRF token missing - this may cause assignment to fail', 'warning');
            }
        }
        
        function goToEmployeesPage() {
            log('Opening employees page in new tab...');
            window.open('/hr/employees/', '_blank');
        }
        
        async function testJavaScriptInEmployeePage() {
            log('Testing JavaScript functions in employees page...');
            
            try {
                // Test if we can call the assignUser function from our debug page
                log('Opening employees page and testing assign user function...');
                
                const testWindow = window.open('/hr/employees/', '_blank');
                
                setTimeout(() => {
                    try {
                        log('Attempting to test assignUser function...');
                        
                        // Check if functions are available
                        if (typeof testWindow.assignUser === 'function') {
                            log('✅ assignUser function is available', 'success');
                        } else {
                            log('❌ assignUser function is NOT available', 'error');
                        }
                        
                        if (typeof testWindow.unassignUser === 'function') {
                            log('✅ unassignUser function is available', 'success');
                        } else {
                            log('❌ unassignUser function is NOT available', 'error');
                        }
                        
                        if (typeof testWindow.bootstrap !== 'undefined') {
                            log('✅ Bootstrap is loaded', 'success');
                        } else {
                            log('❌ Bootstrap is NOT loaded', 'error');
                        }
                        
                    } catch (error) {
                        log(`Cannot access test window (CORS): ${error.message}`, 'warning');
                        log('This is normal for cross-origin windows. Manual testing required.', 'info');
                    }
                }, 3000);
                
            } catch (error) {
                log(`Error testing JavaScript: ${error.message}`, 'error');
            }
        }
        
        function checkBrowserConsole() {
            log('Instructions for checking browser console:', 'info');
            log('1. Press F12 or Ctrl+Shift+I to open Developer Tools');
            log('2. Click on the Console tab');
            log('3. Look for any red error messages');
            log('4. Try clicking Assign User button and watch for errors');
            log('5. Look for "assignUser", "unassignUser" function availability');
        }
        
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            log('User Mapping Debug Tool loaded');
            log('This tool will help identify why the Assign/Unassign User buttons are not working');
            log('User authenticated: """ + str(request.user.is_authenticated).lower() + """');
            if (""" + str(request.user.is_authenticated).lower() + """) {
                log('✅ You are logged in - APIs should work', 'success');
                log('Start by testing the APIs below...');
            } else {
                log('⚠️ You need to log in first for API testing', 'warning');
                log('Click "Login via Admin" button to authenticate');
            }
        });
    </script>
</body>
</html>
    """
    return HttpResponse(debug_html)


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


# Inventory Management module

def inventory_menu(active_href):
    items = [
        {"label": "Dashboard", "href": "/app/inventory"},
        {"label": "STN List", "href": "/app/inventory/stn"},
        {"label": "Create STN", "href": "/app/inventory/stn/new"},
    ]
    for it in items:
        it["active"] = (it["href"] == active_href)
    return items


def module_inventory(request):
    return render_module(request, "Inventory Management", inventory_menu("/app/inventory"), "inventory/inventory_index.html")


def inventory_stn_list(request):
    return render_module(request, "Inventory Management", inventory_menu("/app/inventory/stn"), "inventory/stn_list.html")


def inventory_stn_create(request):
    return render_module(request, "Inventory Management", inventory_menu("/app/inventory/stn/new"), "inventory/stn_create.html")


def inventory_stn_detail(request, id: int):
    return render_module(request, "Inventory Management", inventory_menu("/app/inventory/stn"), "inventory/stn_detail.html")
