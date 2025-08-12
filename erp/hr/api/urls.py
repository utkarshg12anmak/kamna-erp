from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, AccessProfileViewSet, EmployeeDocumentViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='hr-employees')
router.register(r'access-profiles', AccessProfileViewSet, basename='hr-access-profiles')
router.register(r'documents', EmployeeDocumentViewSet, basename='hr-documents')
urlpatterns = router.urls
