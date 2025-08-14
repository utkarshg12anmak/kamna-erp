from rest_framework.routers import DefaultRouter
from .views import STNViewSet, STNDetailViewSet

router = DefaultRouter()
router.register(r'stns', STNViewSet, basename='stns')
router.register(r'stn_lines', STNDetailViewSet, basename='stn-lines')

urlpatterns = router.urls
