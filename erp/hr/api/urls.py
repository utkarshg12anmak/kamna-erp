from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import views with error handling
try:
    from .views import EmployeeViewSet, EmployeeDocumentViewSet, OrgUnitViewSet, PositionViewSet, AccessProfileViewSet
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
    ]
else:
    # Fallback empty urlpatterns if imports fail
    urlpatterns = [] 