from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.db.models import Prefetch
from ..models import Employee, EmployeeDocument, AccessProfile, OrgUnit, Position, HRFieldChange, EmploymentStatus
from .serializers import (EmployeeSerializer, EmployeeListSerializer, EmployeeDocumentSerializer, 
                         AccessProfileSerializer, OrgUnitSerializer, PositionSerializer, HRFieldChangeSerializer)

class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Employee.objects.select_related('manager', 'access_profile', 'user', 'org_unit', 'position')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'status': ['exact'], 
        'department': ['exact'], 
        'designation': ['exact'], 
        'manager': ['exact'], 
        'org_unit': ['exact'], 
        'date_of_joining': ['gte', 'lte'], 
        'gender': ['exact'], 
        'is_phone_assigned': ['exact'], 
        'is_laptop_assigned': ['exact']
    }
    search_fields = ['first_name', 'last_name', 'emp_code', 'email', 'phone', 'pan_number']
    ordering_fields = ['emp_code', 'date_of_joining', 'created_at', 'updated_at']
    ordering = ['emp_code']
    
    def get_serializer_class(self):
        return EmployeeListSerializer if self.action == 'list' else EmployeeSerializer

    def perform_create(self, s):
        s.save(created_by=self.request.user, updated_by=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        instance_before = Employee.objects.get(pk=self.get_object().pk)
        obj = serializer.save(updated_by=self.request.user)
        
        # Field diff logging
        audited_fields = [
            'first_name', 'last_name', 'gender', 'email', 'phone', 'birth_date', 'department', 'designation', 
            'position_id', 'org_unit_id', 'manager_id', 'status', 'date_of_joining', 'salary_amount', 'salary_period', 
            'is_phone_assigned', 'company_assigned_phone_number', 'is_laptop_assigned', 'company_assigned_laptop', 
            'aadhaar_last4', 'pan_number'
        ]
        
        req = self.request
        rid = req.headers.get('X-Request-ID', '')
        ip = (req.META.get('HTTP_X_FORWARDED_FOR') or req.META.get('REMOTE_ADDR'))
        
        for f in audited_fields:
            old = getattr(instance_before, f)
            new = getattr(obj, f)
            if old != new:
                HRFieldChange.objects.create(
                    employee=obj, 
                    field_name=f, 
                    old_value=str(old) if old is not None else '', 
                    new_value=str(new) if new is not None else '', 
                    changed_by=req.user, 
                    source='API', 
                    request_id=rid, 
                    ip_address=ip
                )
        return obj

    @action(detail=True, methods=['post'])
    def soft_delete(self, request, pk=None):
        emp = self.get_object()
        emp.status = EmploymentStatus.EXITED
        emp.save(update_fields=['status', 'updated_at'])
        return Response({'status': 'EXITED'})

    @action(detail=True, methods=['get'])
    def field_changes(self, request, pk=None):
        qs = self.get_object().field_changes.order_by('-changed_at')
        return Response(HRFieldChangeSerializer(qs, many=True).data)

class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = EmployeeDocument.objects.select_related('employee')
    serializer_class = EmployeeDocumentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'doc_type']

class AccessProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = AccessProfile.objects.all()
    serializer_class = AccessProfileSerializer

class OrgUnitViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = OrgUnit.objects.select_related('parent', 'manager')
    serializer_class = OrgUnitSerializer

class PositionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

class OrgChartView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        mode = request.GET.get('mode', 'employee')  # employee|unit
        root_id = request.GET.get('root')
        
        if mode == 'unit':
            def unit_node(u):
                return {
                    'id': u.id,
                    'label': f"{u.name}", 
                    'meta': {'code': u.code, 'type': u.type}, 
                    'children': [unit_node(c) for c in u.children.all()]
                }
            qs = (OrgUnit.objects.filter(parent__isnull=True).prefetch_related('children') 
                  if not root_id else OrgUnit.objects.filter(id=root_id).prefetch_related('children'))
            return Response([unit_node(u) for u in qs])
        else:
            # employee mode
            active = Employee.objects.filter(status=EmploymentStatus.ACTIVE).select_related('position', 'org_unit', 'manager')
            by_manager = {}
            for e in active:
                by_manager.setdefault(e.manager_id, []).append(e)
            
            def emp_node(e):
                kids = by_manager.get(e.id, [])
                return {
                    'id': e.id,
                    'label': f"{e.first_name} {e.last_name} — {e.designation or (e.position.title if e.position else '')}", 
                    'meta': {
                        'emp_code': e.emp_code,
                        'unit': getattr(e.org_unit, 'name', None),
                        'status': e.status
                    }, 
                    'children': [emp_node(k) for k in kids]
                }
            
            roots = ([e for e in active if e.manager_id is None] 
                    if not root_id else [Employee.objects.get(id=root_id)])
            return Response([emp_node(r) for r in roots])
