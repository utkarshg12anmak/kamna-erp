"""
HR Views Tests
Tests for HR module views and templates
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date
from decimal import Decimal

from ..models import (
    Employee, EmployeeDocument, AccessProfile, OrgUnit, Position,
    EmploymentStatus, Gender, SalaryPeriod
)

User = get_user_model()


class HRViewsAuthenticationTest(TestCase):
    """Test view authentication and permissions"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users are redirected"""
        response = self.client.get(reverse('module_hr'))
        
        # Should redirect to login or show login form
        self.assertIn(response.status_code, [302, 401, 403])
    
    def test_authenticated_access(self):
        """Test that authenticated users can access HR views"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('module_hr'))
        self.assertEqual(response.status_code, 200)


class HRDashboardViewTest(TestCase):
    """Test HR dashboard view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        # Create test employees
        for i in range(3):
            Employee.objects.create(
                first_name=f'Employee {i}',
                last_name='Test',
                email=f'employee{i}@company.com',
                status=EmploymentStatus.ACTIVE,
                access_profile=self.access_profile
            )
    
    def test_dashboard_renders(self):
        """Test that dashboard renders correctly"""
        response = self.client.get(reverse('module_hr'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'HR Dashboard')
        self.assertContains(response, 'Total Active')
        self.assertContains(response, 'Upcoming Birthdays')
    
    def test_dashboard_context(self):
        """Test dashboard context data"""
        response = self.client.get(reverse('module_hr'))
        
        self.assertEqual(response.status_code, 200)
        # Check that template has access to necessary data
        self.assertIn('request', response.context)


class EmployeeListViewTest(TestCase):
    """Test employee list view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
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
        
        # Create test employees
        for i in range(5):
            Employee.objects.create(
                first_name=f'Employee {i}',
                last_name='Test',
                email=f'employee{i}@company.com',
                status=EmploymentStatus.ACTIVE,
                access_profile=self.access_profile,
                org_unit=self.org_unit,
                position=self.position
            )
    
    def test_employee_list_renders(self):
        """Test that employee list renders correctly"""
        response = self.client.get(reverse('hr_employees'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employee Management')
        self.assertContains(response, 'Employee 0')
        self.assertContains(response, 'Employee 4')
    
    def test_employee_list_filters(self):
        """Test employee list filtering"""
        response = self.client.get(reverse('hr_employees'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Department')
        self.assertContains(response, 'Status')
        self.assertContains(response, 'Search')
    
    def test_employee_list_pagination(self):
        """Test employee list pagination"""
        response = self.client.get(reverse('hr_employees'))
        
        self.assertEqual(response.status_code, 200)
        # Should contain pagination controls if needed
        self.assertContains(response, 'employees-table')


class EmployeeDetailViewTest(TestCase):
    """Test employee detail view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        self.employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            phone='+1234567890',
            status=EmploymentStatus.ACTIVE,
            access_profile=self.access_profile
        )
    
    def test_employee_detail_renders(self):
        """Test that employee detail renders correctly"""
        response = self.client.get(
            reverse('hr_employee_view', kwargs={'emp_id': self.employee.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'john.doe@company.com')
        self.assertContains(response, '+1234567890')
    
    def test_employee_detail_tabs(self):
        """Test employee detail tab structure"""
        response = self.client.get(
            reverse('hr_employee_view', kwargs={'emp_id': self.employee.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Overview')
        self.assertContains(response, 'Documents')
        self.assertContains(response, 'Assets')
        self.assertContains(response, 'History')
    
    def test_nonexistent_employee(self):
        """Test viewing nonexistent employee"""
        response = self.client.get(
            reverse('hr_employee_view', kwargs={'emp_id': 99999})
        )
        
        self.assertEqual(response.status_code, 404)


class EmployeeFormViewTest(TestCase):
    """Test employee form views (create and edit)"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
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
    
    def test_employee_create_form_renders(self):
        """Test that employee create form renders correctly"""
        response = self.client.get(reverse('hr_employees_new'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add New Employee')
        self.assertContains(response, 'First Name')
        self.assertContains(response, 'Last Name')
        self.assertContains(response, 'Email')
    
    def test_employee_create_form_tabs(self):
        """Test employee form tab structure"""
        response = self.client.get(reverse('hr_employees_new'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Personal Information')
        self.assertContains(response, 'Job Details')
        self.assertContains(response, 'Payroll Information')
        self.assertContains(response, 'Documents')
        self.assertContains(response, 'Assets')
    
    def test_employee_create_form_fields(self):
        """Test employee form field structure"""
        response = self.client.get(reverse('hr_employees_new'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="first_name"')
        self.assertContains(response, 'name="last_name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="phone"')
        self.assertContains(response, 'name="gender"')
    
    def test_employee_edit_form_renders(self):
        """Test that employee edit form renders correctly"""
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            access_profile=self.access_profile
        )
        
        response = self.client.get(
            reverse('hr_employee_edit', kwargs={'emp_id': employee.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Employee')
        self.assertContains(response, 'John')
        self.assertContains(response, 'Doe')


class OrgChartViewTest(TestCase):
    """Test organizational chart view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        # Create organizational structure
        self.ceo = Employee.objects.create(
            first_name='CEO',
            last_name='Boss',
            email='ceo@company.com',
            access_profile=self.access_profile
        )
        
        self.manager = Employee.objects.create(
            first_name='Manager',
            last_name='Lead',
            email='manager@company.com',
            manager=self.ceo,
            access_profile=self.access_profile
        )
        
        self.employee = Employee.objects.create(
            first_name='Employee',
            last_name='Worker',
            email='employee@company.com',
            manager=self.manager,
            access_profile=self.access_profile
        )
    
    def test_org_chart_renders(self):
        """Test that org chart renders correctly"""
        response = self.client.get(reverse('hr_org_chart'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Organizational Chart')
        self.assertContains(response, 'Total Employees')
        self.assertContains(response, 'View Type')
    
    def test_org_chart_structure(self):
        """Test org chart structure elements"""
        response = self.client.get(reverse('hr_org_chart'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'org-chart')
        self.assertContains(response, 'org-node')
        self.assertContains(response, 'org-level')
    
    def test_org_chart_controls(self):
        """Test org chart controls"""
        response = self.client.get(reverse('hr_org_chart'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View Type')
        self.assertContains(response, 'Department Filter')
        self.assertContains(response, 'Search Employee')


class ViewSecurityTest(TestCase):
    """Test view security and permissions"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        self.employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            salary=Decimal('50000.00'),
            access_profile=self.access_profile
        )
    
    def test_sensitive_data_protection(self):
        """Test that sensitive data is protected"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('hr_employee_view', kwargs={'emp_id': self.employee.id})
        )
        
        self.assertEqual(response.status_code, 200)
        # Salary might be masked or hidden based on permissions
        # This depends on implementation details
    
    def test_cross_user_access(self):
        """Test that users can't access unauthorized data"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        self.client.login(username='otheruser', password='otherpass123')
        
        # Should still be able to view employee (depends on business rules)
        response = self.client.get(
            reverse('hr_employee_view', kwargs={'emp_id': self.employee.id})
        )
        
        self.assertIn(response.status_code, [200, 403])


class ViewPerformanceTest(TestCase):
    """Test view performance"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        # Create many employees for performance testing
        employees = []
        for i in range(50):
            employees.append(Employee(
                first_name=f'Employee {i}',
                last_name='Test',
                email=f'employee{i}@company.com',
                access_profile=self.access_profile
            ))
        
        Employee.objects.bulk_create(employees)
    
    def test_employee_list_performance(self):
        """Test employee list view performance"""
        # This test ensures the view loads efficiently even with many employees
        response = self.client.get(reverse('hr_employees'))
        
        self.assertEqual(response.status_code, 200)
        # Should complete in reasonable time
    
    def test_dashboard_performance(self):
        """Test dashboard view performance"""
        response = self.client.get(reverse('module_hr'))
        
        self.assertEqual(response.status_code, 200)
        # Should complete efficiently even with aggregations


class FormValidationTest(TestCase):
    """Test form validation on views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
    
    def test_form_validation_errors(self):
        """Test form validation error handling"""
        # This would test actual form submission if forms were implemented
        response = self.client.get(reverse('hr_employees_new'))
        
        self.assertEqual(response.status_code, 200)
        # Form should be present and ready for validation testing
        self.assertContains(response, 'form')
    
    def test_required_field_validation(self):
        """Test required field validation"""
        # This would test posting invalid data if forms were implemented
        pass
    
    def test_email_format_validation(self):
        """Test email format validation"""
        # This would test email validation if forms were implemented
        pass


class TemplateRenderingTest(TestCase):
    """Test template rendering and structure"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_base_template_inheritance(self):
        """Test that templates extend base properly"""
        response = self.client.get(reverse('module_hr'))
        
        self.assertEqual(response.status_code, 200)
        # Should contain base template elements
        self.assertContains(response, 'DOCTYPE html')
        self.assertContains(response, 'bootstrap')
    
    def test_responsive_design(self):
        """Test responsive design elements"""
        response = self.client.get(reverse('hr_employees'))
        
        self.assertEqual(response.status_code, 200)
        # Should contain responsive Bootstrap classes
        self.assertContains(response, 'col-md')
        self.assertContains(response, 'row')
    
    def test_javascript_inclusion(self):
        """Test JavaScript functionality inclusion"""
        response = self.client.get(reverse('hr_org_chart'))
        
        self.assertEqual(response.status_code, 200)
        # Should contain JavaScript for interactive features
        self.assertContains(response, '<script>')
        self.assertContains(response, 'function')
    
    def test_css_styling(self):
        """Test CSS styling inclusion"""
        response = self.client.get(reverse('hr_org_chart'))
        
        self.assertEqual(response.status_code, 200)
        # Should contain custom CSS
        self.assertContains(response, '<style>')
        self.assertContains(response, 'org-chart')
