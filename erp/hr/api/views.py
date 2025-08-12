from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model
from ..models import Employee, EmployeeDocument, AccessProfile, EmploymentStatus
from .serializers import EmployeeSerializer, EmployeeListSerializer, AccessProfileSerializer, EmployeeDocumentSerializer

User = get_user_model()

class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAuthenticated]
    queryset = Employee.objects.select_related('manager','access_profile','user')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {'status':['exact'],'department':['exact'],'designation':['exact'],'manager':['exact'],'date_of_joining':['gte','lte']}
    search_fields = ['first_name','last_name','emp_code','email','phone','pan_number']
    ordering_fields = ['emp_code','date_of_joining','created_at','updated_at']
    ordering = ['emp_code']

    def get_serializer_class(self):
        return EmployeeListSerializer if self.action=='list' else EmployeeSerializer

    def perform_create(self, s):
        s.save(created_by=self.request.user, updated_by=self.request.user)
    def perform_update(self, s):
        s.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def soft_delete(self, request, pk=None):
        emp = self.get_object()
        emp.status = EmploymentStatus.EXITED
        emp.save(update_fields=['status','updated_at'])
        return Response({'status':'EXITED'})

    @action(detail=True, methods=['post'])
    def link_user(self, request, pk=None):
        emp = self.get_object()
        user_id = request.data.get('user_id')
        username = request.data.get('username')
        user = None
        if user_id:
            user = User.objects.filter(id=user_id).first()
        elif username:
            user = User.objects.filter(username=username).first()
        if not user:
            return Response({'detail':'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        emp.user = user
        emp.save(update_fields=['user'])
        return Response({'linked_user': user.username})

class AccessProfileViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAuthenticated]
    queryset = AccessProfile.objects.all()
    serializer_class = AccessProfileSerializer

class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAuthenticated]
    queryset = EmployeeDocument.objects.select_related('employee')
    serializer_class = EmployeeDocumentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {'employee':['exact'],'doc_type':['exact']}
    search_fields = ['number','notes']
    ordering = ['-created_at']
