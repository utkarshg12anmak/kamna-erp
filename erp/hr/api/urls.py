from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import views with error handling
try:
    from .views import EmployeeViewSet, EmployeeDocumentViewSet, OrgUnitViewSet, PositionViewSet, AccessProfileViewSet
    from .dashboard import HRDashboardSummary, HRDashboardUpcoming, HRDashboardOrgChart
    views_imported = True
except ImportError as e:
    print(f"Warning: Could not import HR API views: {e}")
    views_imported = False

# Create router and register viewsets only if views imported successfully
if views_imported:
    router = DefaultRouter()
    router.register(r'employees', EmployeeViewSet)
    router.register(r'employee-documents', EmployeeDocumentViewSet)
    router.register(r'org-units', OrgUnitViewSet)
    router.register(r'positions', PositionViewSet)
    router.register(r'access-profiles', AccessProfileViewSet)
    
    urlpatterns = [
        path('', include(router.urls)),
        path('dashboard/summary/', HRDashboardSummary.as_view(), name='hr-dashboard-summary'),
        path('dashboard/upcoming/', HRDashboardUpcoming.as_view(), name='hr-dashboard-upcoming'),
        path('dashboard/org-chart/', HRDashboardOrgChart.as_view(), name='hr-dashboard-org-chart'),
    ]
else:
    # Fallback empty urlpatterns if imports fail
    urlpatterns = [] 