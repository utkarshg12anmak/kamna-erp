from rest_framework.routers import DefaultRouter
from .views import (CvHubEntryViewSet, CvHubGSTRegistrationViewSet, CvHubAddressViewSet,
                    CvHubContactViewSet, CvHubStateViewSet, CvHubCityViewSet)

router = DefaultRouter()
router.register(r'entries', CvHubEntryViewSet, basename='cv_hub_entries')
router.register(r'registrations', CvHubGSTRegistrationViewSet, basename='cv_hub_registrations')
router.register(r'addresses', CvHubAddressViewSet, basename='cv_hub_addresses')
router.register(r'contacts', CvHubContactViewSet, basename='cv_hub_contacts')
router.register(r'states', CvHubStateViewSet, basename='cv_hub_states')
router.register(r'cities', CvHubCityViewSet, basename='cv_hub_cities')

urlpatterns = router.urls
