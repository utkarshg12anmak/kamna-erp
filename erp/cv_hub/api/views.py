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

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user if self.request.user.is_authenticated else None)

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

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        from django.contrib.contenttypes.models import ContentType
        entry = self.get_object()
        
        # Get history from all related models
        entry_ct = ContentType.objects.get_for_model(CvHubEntry)
        reg_ct = ContentType.objects.get_for_model(CvHubGSTRegistration)
        addr_ct = ContentType.objects.get_for_model(CvHubAddress)
        contact_ct = ContentType.objects.get_for_model(CvHubContact)
        
        history_data = []
        
        # Entry history
        for h in entry.history.all().order_by('-history_date')[:10]:
            history_data.append({
                'date': h.history_date,
                'type': h.history_type,
                'model': 'Entry',
                'object_id': h.id,
                'changes': self._get_field_changes(h),
                'user': h.history_user.username if h.history_user else 'System'
            })
        
        # Related model histories
        for reg in entry.registrations.all():
            for h in reg.history.all().order_by('-history_date')[:5]:
                history_data.append({
                    'date': h.history_date,
                    'type': h.history_type,
                    'model': 'GST Registration',
                    'object_id': h.id,
                    'changes': self._get_field_changes(h),
                    'user': h.history_user.username if h.history_user else 'System'
                })
        
        for addr in entry.addresses.all():
            for h in addr.history.all().order_by('-history_date')[:5]:
                history_data.append({
                    'date': h.history_date,
                    'type': h.history_type,
                    'model': 'Address',
                    'object_id': h.id,
                    'changes': self._get_field_changes(h),
                    'user': h.history_user.username if h.history_user else 'System'
                })
        
        for contact in entry.contacts.all():
            for h in contact.history.all().order_by('-history_date')[:5]:
                history_data.append({
                    'date': h.history_date,
                    'type': h.history_type,
                    'model': 'Contact',
                    'object_id': h.id,
                    'changes': self._get_field_changes(h),
                    'user': h.history_user.username if h.history_user else 'System'
                })
        
        # Sort by date descending
        history_data.sort(key=lambda x: x['date'], reverse=True)
        
        return Response(history_data[:20])  # Return latest 20 entries
    
    def _get_field_changes(self, history_record):
        """Get human-readable field changes"""
        if history_record.history_type == '+':
            return 'Created'
        elif history_record.history_type == '-':
            return 'Deleted'
        elif history_record.history_type == '~':
            try:
                # Get the previous record
                prev_record = history_record.prev_record
                if prev_record:
                    changes = []
                    # Compare key fields
                    for field in ['legal_name', 'trade_name', 'status', 'constitution', 'website', 'gstin', 'phone', 'email', 'line1', 'first_name', 'last_name']:
                        if hasattr(history_record, field) and hasattr(prev_record, field):
                            old_val = getattr(prev_record, field, '')
                            new_val = getattr(history_record, field, '')
                            if old_val != new_val:
                                changes.append(f"{field}: {old_val} → {new_val}")
                    return '; '.join(changes) if changes else 'Updated'
            except:
                pass
            return 'Updated'
        return 'Unknown'

class CvHubGSTRegistrationViewSet(viewsets.ModelViewSet):
    queryset = CvHubGSTRegistration.objects.select_related('entry')
    serializer_class = CvHubGSTRegistrationSerializer
    filter_backends=[DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields={'entry':['exact'],'taxpayer_type':['exact'],'gstin_status':['exact'],'is_primary':['exact']}
    search_fields=['gstin','legal_name_of_business','trade_name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user if self.request.user.is_authenticated else None)

class CvHubAddressViewSet(viewsets.ModelViewSet):
    queryset = CvHubAddress.objects.select_related('entry','state','city')
    serializer_class = CvHubAddressSerializer
    filter_backends=[DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields={'entry':['exact'],'type':['exact'],'is_default_billing':['exact'],'is_default_shipping':['exact'],'state':['exact'],'city':['exact']}
    search_fields=['line1','line2','pincode']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user if self.request.user.is_authenticated else None)

class CvHubContactViewSet(viewsets.ModelViewSet):
    queryset = CvHubContact.objects.select_related('entry')
    serializer_class = CvHubContactSerializer
    filter_backends=[DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields={'entry':['exact'],'is_primary':['exact'],'designation':['exact']}
    search_fields=['first_name','last_name','phone','email']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user if self.request.user.is_authenticated else None)

class CvHubStateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CvHubState.objects.all().order_by('name')
    serializer_class = CvHubStateSerializer

class CvHubCityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CvHubCitySerializer
    def get_queryset(self):
        qs = CvHubCity.objects.all().order_by('name')
        st = self.request.GET.get('state')
        return qs.filter(state_id=st) if st else qs
