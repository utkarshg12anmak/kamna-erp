from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ..models import (CvHubEntry, CvHubGSTRegistration, CvHubAddress, CvHubContact,
                      CvHubState, CvHubCity)
from .serializers import (CvHubEntrySerializer, CvHubEntryDetailSerializer, CvHubGSTRegistrationSerializer,
                          CvHubAddressSerializer, CvHubContactSerializer, CvHubStateSerializer, CvHubCitySerializer)

class CvHubEntryViewSet(viewsets.ModelViewSet):
    queryset = CvHubEntry.objects.all().prefetch_related('registrations','addresses','contacts')
    filter_backends=[DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields={'status':['exact'],'constitution':['exact'],'is_customer':['exact'],'is_supplier':['exact'],'is_vendor':['exact'],'is_logistics':['exact'],'for_sales':['exact'],'for_purchase':['exact'],'addresses__state':['exact'],'addresses__city':['exact'],'registrations__taxpayer_type':['exact']}
    search_fields=['legal_name','trade_name','registrations__gstin','contacts__phone','contacts__email','addresses__city__name','addresses__state__name']
    ordering_fields=['legal_name','updated_at','created_at']
    ordering=['legal_name']
    def get_serializer_class(self):
        return CvHubEntryDetailSerializer if self.action=='retrieve' else CvHubEntrySerializer

    @action(detail=False, methods=['get'])
    def quick(self, request):
        q = request.GET.get('q','')
        qs = self.filter_queryset(self.get_queryset())
        if q: qs = qs.filter(legal_name__icontains=q)[:20]
        data = [{'id':e.id,'legal_name':e.legal_name,'trade_name':e.trade_name,'primary_gstin': (e.registrations.filter(is_primary=True).first().gstin if e.registrations.filter(is_primary=True).exists() else None)} for e in qs]
        return Response(data)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        e = self.get_object()
        primary_reg = e.registrations.filter(is_primary=True).first()
        billing = e.addresses.filter(is_default_billing=True).first()
        shipping= e.addresses.filter(is_default_shipping=True).first()
        primary_contact = e.contacts.filter(is_primary=True).first()
        return Response({
            'commerce_label': 'Both' if (e.for_sales and e.for_purchase) else ('Sales' if e.for_sales else ('Purchase' if e.for_purchase else '—')),
            'primary_gstin': getattr(primary_reg,'gstin',None),
            'billing': CvHubAddressSerializer(billing).data if billing else None,
            'shipping': CvHubAddressSerializer(shipping).data if shipping else None,
            'primary_contact': CvHubContactSerializer(primary_contact).data if primary_contact else None
        })

class CvHubGSTRegistrationViewSet(viewsets.ModelViewSet):
    queryset = CvHubGSTRegistration.objects.select_related('entry')
    serializer_class = CvHubGSTRegistrationSerializer
    filter_backends=[DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields={'entry':['exact'],'taxpayer_type':['exact'],'gstin_status':['exact'],'is_primary':['exact']}
    search_fields=['gstin','legal_name_of_business','trade_name']

class CvHubAddressViewSet(viewsets.ModelViewSet):
    queryset = CvHubAddress.objects.select_related('entry','state','city')
    serializer_class = CvHubAddressSerializer
    filter_backends=[DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields={'entry':['exact'],'type':['exact'],'is_default_billing':['exact'],'is_default_shipping':['exact'],'state':['exact'],'city':['exact']}
    search_fields=['line1','line2','pincode']

class CvHubContactViewSet(viewsets.ModelViewSet):
    queryset = CvHubContact.objects.select_related('entry')
    serializer_class = CvHubContactSerializer
    filter_backends=[DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields={'entry':['exact'],'is_primary':['exact']}
    search_fields=['full_name','phone','email']

class CvHubStateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CvHubState.objects.all().order_by('name')
    serializer_class = CvHubStateSerializer

class CvHubCityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CvHubCitySerializer
    def get_queryset(self):
        qs = CvHubCity.objects.all().order_by('name')
        st = self.request.GET.get('state')
        return qs.filter(state_id=st) if st else qs
