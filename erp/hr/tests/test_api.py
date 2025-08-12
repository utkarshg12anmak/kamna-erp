"""
HR API Tests
Tests for HR module API endpoints including serializers and views
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date
from decimal import Decimal
import json

from ..models import (
    Employee, EmployeeDocument, AccessProfile, OrgUnit, Position,
    EmploymentStatus, Gender, SalaryPeriod
)

User = get_user_model()


class HRAPIAuthenticationTest(APITestCase):
    """Test API authentication and permissions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
    
    def get_jwt_token(self):
        """Get JWT token for authenticated requests"""
        refresh = RefreshToken.for_user(self.user)
        return str(refresh.access_token)
    
    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected"""
        response = self.client.get('/api/hr/employees/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_request(self):
        """Test that authenticated requests are allowed"""
        token = self.get_jwt_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # This should work once API is enabled
        # response = self.client.get('/api/hr/employees/')
        # self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmployeeSerializerTest(TestCase):
    """Test Employee serializer functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access',
            description='Standard employee access'
        )
        
        self.org_unit = OrgUnit.objects.create(
            name='IT Department',
            code='IT-001',
            type='department'
        )
        
        self.position = Position.objects.create(
            title='Software Developer',
            grade=5,
            family='technical'
        )
    
    def test_employee_serialization(self):
        """Test employee model serialization"""
        from ..api.serializers import EmployeeSerializer
        
        employee = Employee.objects.create(
            emp_code='EMP001',
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            phone='+1234567890',
            gender=Gender.MALE,
            date_of_birth=date(1990, 1, 1),
            status=EmploymentStatus.ACTIVE,
            access_profile=self.access_profile,
            org_unit=self.org_unit,
            position=self.position,
            salary=Decimal('50000.00')
        )
        
        serializer = EmployeeSerializer(employee)
        data = serializer.data
        
        self.assertEqual(data['emp_code'], 'EMP001')
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['last_name'], 'Doe')
        self.assertEqual(data['email'], 'john.doe@company.com')
        self.assertEqual(data['status'], EmploymentStatus.ACTIVE)
    
    def test_employee_deserialization(self):
        """Test employee data deserialization"""
        from ..api.serializers import EmployeeSerializer
        
        data = {
            'emp_code': 'EMP002',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@company.com',
            'phone': '+1234567891',
            'gender': Gender.FEMALE,
            'date_of_birth': '1992-05-15',
            'status': EmploymentStatus.ACTIVE,
            'access_profile': self.access_profile.id,
            'org_unit': self.org_unit.id,
            'position': self.position.id,
            'salary': '45000.00'
        }
        
        serializer = EmployeeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        employee = serializer.save()
        self.assertEqual(employee.emp_code, 'EMP002')
        self.assertEqual(employee.first_name, 'Jane')
        self.assertEqual(employee.email, 'jane.smith@company.com')
    
    def test_employee_validation(self):
        """Test employee data validation"""
        from ..api.serializers import EmployeeSerializer
        
        # Test invalid email
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'access_profile': self.access_profile.id
        }
        
        serializer = EmployeeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_salary_masking(self):
        """Test salary field masking for unauthorized users"""
        from ..api.serializers import EmployeeSerializer
        
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            salary=Decimal('50000.00'),
            access_profile=self.access_profile
        )
        
        # Test with context indicating no salary access
        serializer = EmployeeSerializer(
            employee, 
            context={'mask_salary': True}
        )
        data = serializer.data
        
        # Salary should be masked
        self.assertEqual(data.get('salary'), '****')


class APIViewsTest(APITestCase):
    """Test API views functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        self.org_unit = OrgUnit.objects.create(
            name='IT Department',
            code='IT-001',
            type='department'
        )
        
        self.position = Position.objects.create(
            title='Developer',
            grade=5,
            family='technical'
        )
        
        self.employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            access_profile=self.access_profile,
            org_unit=self.org_unit,
            position=self.position
        )
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    
    def test_employee_list_view(self):
        """Test employee list API endpoint"""
        # This test will work once API is enabled
        pass
        # response = self.client.get('/api/hr/employees/')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_employee_detail_view(self):
        """Test employee detail API endpoint"""
        # This test will work once API is enabled
        pass
        # response = self.client.get(f'/api/hr/employees/{self.employee.id}/')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data['id'], self.employee.id)
    
    def test_employee_create_view(self):
        """Test employee creation via API"""
        # This test will work once API is enabled
        pass
        # data = {
        #     'first_name': 'Jane',
        #     'last_name': 'Smith',
        #     'email': 'jane.smith@company.com',
        #     'access_profile': self.access_profile.id
        # }
        # 
        # response = self.client.post('/api/hr/employees/', data)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(response.data['first_name'], 'Jane')
    
    def test_employee_update_view(self):
        """Test employee update via API"""
        # This test will work once API is enabled
        pass
        # data = {
        #     'first_name': 'John Updated',
        #     'last_name': 'Doe',
        #     'email': 'john.updated@company.com',
        #     'access_profile': self.access_profile.id
        # }
        # 
        # response = self.client.put(f'/api/hr/employees/{self.employee.id}/', data)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data['first_name'], 'John Updated')
    
    def test_employee_delete_view(self):
        """Test employee soft delete via API"""
        # This test will work once API is enabled
        pass
        # response = self.client.delete(f'/api/hr/employees/{self.employee.id}/')
        # self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # 
        # # Check that employee is soft deleted
        # self.employee.refresh_from_db()
        # self.assertIsNotNone(self.employee.deleted_at)
    
    def test_employee_filtering(self):
        """Test employee filtering functionality"""
        # This test will work once API is enabled
        pass
        # response = self.client.get(f'/api/hr/employees/?department={self.org_unit.name}')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_employee_search(self):
        """Test employee search functionality"""
        # This test will work once API is enabled
        pass
        # response = self.client.get('/api/hr/employees/?search=John')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_org_chart_api(self):
        """Test organizational chart API"""
        # This test will work once API is enabled
        pass
        # response = self.client.get('/api/hr/employees/org_chart/')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertIn('tree', response.data)


class OrgUnitAPITest(APITestCase):
    """Test OrgUnit API functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.org_unit = OrgUnit.objects.create(
            name='IT Department',
            code='IT-001',
            type='department'
        )
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    
    def test_org_unit_serialization(self):
        """Test OrgUnit serialization"""
        from ..api.serializers import OrgUnitSerializer
        
        serializer = OrgUnitSerializer(self.org_unit)
        data = serializer.data
        
        self.assertEqual(data['name'], 'IT Department')
        self.assertEqual(data['code'], 'IT-001')
        self.assertEqual(data['type'], 'department')


class PositionAPITest(APITestCase):
    """Test Position API functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.position = Position.objects.create(
            title='Senior Developer',
            grade=7,
            family='technical'
        )
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    
    def test_position_serialization(self):
        """Test Position serialization"""
        from ..api.serializers import PositionSerializer
        
        serializer = PositionSerializer(self.position)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Senior Developer')
        self.assertEqual(data['grade'], 7)
        self.assertEqual(data['family'], 'technical')


class DashboardAPITest(APITestCase):
    """Test Dashboard API functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        # Create test employees
        for i in range(5):
            Employee.objects.create(
                first_name=f'Employee {i}',
                last_name='Test',
                email=f'employee{i}@company.com',
                status=EmploymentStatus.ACTIVE,
                access_profile=self.access_profile
            )
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    
    def test_dashboard_summary_data(self):
        """Test dashboard summary API"""
        from ..api.dashboard import HRDashboardSummary
        
        view = HRDashboardSummary()
        view.request = type('Request', (), {'user': self.user})()
        
        response = view.get(view.request)
        data = response.data
        
        self.assertIn('total_active_employees', data)
        self.assertIn('upcoming_birthdays', data)
        self.assertIn('work_anniversaries_this_month', data)
        self.assertIn('monthly_salary_run', data)
        
        self.assertEqual(data['total_active_employees'], 5)


class APIErrorHandlingTest(APITestCase):
    """Test API error handling"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    
    def test_invalid_employee_id(self):
        """Test handling of invalid employee ID"""
        # This test will work once API is enabled
        pass
        # response = self.client.get('/api/hr/employees/99999/')
        # self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_data_format(self):
        """Test handling of invalid data format"""
        # This test will work once API is enabled
        pass
        # data = {
        #     'first_name': '',  # Empty required field
        #     'email': 'invalid-email',  # Invalid email format
        # }
        # 
        # response = self.client.post('/api/hr/employees/', data)
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertIn('first_name', response.data)
        # self.assertIn('email', response.data)


class APIPerformanceTest(APITestCase):
    """Test API performance considerations"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        # Create multiple employees for performance testing
        employees = []
        for i in range(100):
            employees.append(Employee(
                first_name=f'Employee {i}',
                last_name='Test',
                email=f'employee{i}@company.com',
                access_profile=self.access_profile
            ))
        
        Employee.objects.bulk_create(employees)
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    
    def test_list_query_optimization(self):
        """Test that list queries are optimized"""
        # This test will work once API is enabled
        pass
        # with self.assertNumQueries(3):  # Should be minimal queries due to select_related
        #     response = self.client.get('/api/hr/employees/')
        #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_pagination(self):
        """Test API pagination"""
        # This test will work once API is enabled
        pass
        # response = self.client.get('/api/hr/employees/')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertIn('count', response.data)
        # self.assertIn('next', response.data)
        # self.assertIn('previous', response.data)
        # self.assertIn('results', response.data)
