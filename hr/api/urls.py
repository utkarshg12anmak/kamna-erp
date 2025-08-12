from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, AccessProfileViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='hr-employees')
router.register(r'access-profiles', AccessProfileViewSet, basename='hr-access-profiles')
urlpatterns = router.urls
