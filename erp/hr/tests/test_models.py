"""
HR Models Tests
Tests for HR module models including Employee, OrgUnit, Position, etc.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from datetime import date, timedelta
from decimal import Decimal

from ..models import (
    Employee, EmployeeDocument, AccessProfile, OrgUnit, Position, 
    HRFieldChange, EmploymentStatus, Gender, SalaryPeriod
)

User = get_user_model()


class EmployeeModelTest(TestCase):
    """Test Employee model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
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
    
    def test_employee_creation(self):
        """Test creating a new employee"""
        employee = Employee.objects.create(
            user=self.user,
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
            salary=Decimal('50000.00'),
            salary_period=SalaryPeriod.MONTHLY
        )
        
        self.assertEqual(employee.full_name, 'John Doe')
        self.assertEqual(employee.emp_code, 'EMP001')
        self.assertEqual(employee.status, EmploymentStatus.ACTIVE)
        self.assertTrue(employee.is_active)
    
    def test_employee_auto_emp_code(self):
        """Test automatic employee code generation"""
        employee = Employee.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@company.com',
            access_profile=self.access_profile
        )
        
        self.assertIsNotNone(employee.emp_code)
        self.assertTrue(employee.emp_code.startswith('EMP'))
    
    def test_employee_unique_constraints(self):
        """Test unique constraints on employee fields"""
        Employee.objects.create(
            user=self.user,
            emp_code='EMP001',
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            access_profile=self.access_profile
        )
        
        # Test duplicate emp_code
        with self.assertRaises(IntegrityError):
            Employee.objects.create(
                emp_code='EMP001',
                first_name='Jane',
                last_name='Smith',
                email='jane.smith@company.com',
                access_profile=self.access_profile
            )
    
    def test_employee_manager_hierarchy(self):
        """Test employee manager hierarchy"""
        manager = Employee.objects.create(
            first_name='Manager',
            last_name='Boss',
            email='manager@company.com',
            access_profile=self.access_profile
        )
        
        employee = Employee.objects.create(
            first_name='Employee',
            last_name='Worker',
            email='employee@company.com',
            manager=manager,
            access_profile=self.access_profile
        )
        
        self.assertEqual(employee.manager, manager)
        self.assertIn(employee, manager.direct_reports.all())
    
    def test_employee_soft_delete(self):
        """Test employee soft delete functionality"""
        employee = Employee.objects.create(
            first_name='Test',
            last_name='Employee',
            email='test@company.com',
            access_profile=self.access_profile
        )
        
        employee.delete()
        
        # Employee should still exist but be marked as deleted
        employee.refresh_from_db()
        self.assertIsNotNone(employee.deleted_at)
        self.assertFalse(employee.is_active)
    
    def test_employee_pan_validation(self):
        """Test PAN number validation and formatting"""
        employee = Employee.objects.create(
            first_name='Test',
            last_name='Employee',
            email='test@company.com',
            pan_number='abcde1234f',  # lowercase
            access_profile=self.access_profile
        )
        
        # PAN should be converted to uppercase
        self.assertEqual(employee.pan_number, 'ABCDE1234F')


class OrgUnitModelTest(TestCase):
    """Test OrgUnit model functionality"""
    
    def test_org_unit_creation(self):
        """Test creating organizational units"""
        parent = OrgUnit.objects.create(
            name='Company',
            code='COMP-001',
            type='company'
        )
        
        child = OrgUnit.objects.create(
            name='IT Department',
            code='IT-001',
            type='department',
            parent=parent
        )
        
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())
    
    def test_org_unit_hierarchy_validation(self):
        """Test organizational unit hierarchy validation"""
        unit1 = OrgUnit.objects.create(
            name='Unit 1',
            code='UNIT-001',
            type='department'
        )
        
        unit2 = OrgUnit.objects.create(
            name='Unit 2',
            code='UNIT-002',
            type='department',
            parent=unit1
        )
        
        # Try to create circular reference
        unit1.parent = unit2
        with self.assertRaises(ValidationError):
            unit1.full_clean()


class PositionModelTest(TestCase):
    """Test Position model functionality"""
    
    def test_position_creation(self):
        """Test creating positions"""
        position = Position.objects.create(
            title='Senior Developer',
            grade=7,
            family='technical'
        )
        
        self.assertEqual(position.title, 'Senior Developer')
        self.assertEqual(position.grade, 7)
        self.assertEqual(position.family, 'technical')


class AccessProfileModelTest(TestCase):
    """Test AccessProfile model functionality"""
    
    def test_access_profile_creation(self):
        """Test creating access profiles"""
        profile = AccessProfile.objects.create(
            name='Manager Access',
            description='Access profile for managers'
        )
        
        self.assertEqual(profile.name, 'Manager Access')
        self.assertTrue(profile.is_active)


class HRFieldChangeModelTest(TestCase):
    """Test HRFieldChange audit model"""
    
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
        
        self.employee = Employee.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            access_profile=self.access_profile
        )
    
    def test_field_change_logging(self):
        """Test field change audit logging"""
        change = HRFieldChange.objects.create(
            employee=self.employee,
            field_name='salary',
            old_value='50000.00',
            new_value='55000.00',
            changed_by=self.user,
            change_reason='Annual increment'
        )
        
        self.assertEqual(change.employee, self.employee)
        self.assertEqual(change.field_name, 'salary')
        self.assertEqual(change.old_value, '50000.00')
        self.assertEqual(change.new_value, '55000.00')
        self.assertEqual(change.changed_by, self.user)


class EmployeeDocumentModelTest(TestCase):
    """Test EmployeeDocument model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        self.employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            access_profile=self.access_profile
        )
    
    def test_employee_document_creation(self):
        """Test creating employee documents"""
        document = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type='passport',
            document_name='Passport Copy',
            file_path='/documents/passport.pdf'
        )
        
        self.assertEqual(document.employee, self.employee)
        self.assertEqual(document.document_type, 'passport')
        self.assertEqual(document.document_name, 'Passport Copy')


class ModelValidationTest(TestCase):
    """Test model validation and business rules"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
    
    def test_email_validation(self):
        """Test email field validation"""
        with self.assertRaises(ValidationError):
            employee = Employee(
                first_name='John',
                last_name='Doe',
                email='invalid-email',  # Invalid email
                access_profile=self.access_profile
            )
            employee.full_clean()
    
    def test_phone_validation(self):
        """Test phone number validation"""
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            phone='+1234567890',
            access_profile=self.access_profile
        )
        
        self.assertEqual(employee.phone, '+1234567890')
    
    def test_date_validation(self):
        """Test date field validation"""
        future_date = date.today() + timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            employee = Employee(
                first_name='John',
                last_name='Doe',
                email='john@company.com',
                date_of_birth=future_date,  # Future birth date
                access_profile=self.access_profile
            )
            employee.full_clean()


class ModelMethodsTest(TestCase):
    """Test model methods and properties"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
        
        self.employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            date_of_birth=date(1990, 1, 1),
            access_profile=self.access_profile
        )
    
    def test_age_calculation(self):
        """Test age calculation method"""
        expected_age = date.today().year - 1990
        if date.today() < date(date.today().year, 1, 1):
            expected_age -= 1
        
        self.assertEqual(self.employee.age, expected_age)
    
    def test_full_name_property(self):
        """Test full name property"""
        self.assertEqual(self.employee.full_name, 'John Doe')
    
    def test_is_active_property(self):
        """Test is_active property"""
        self.assertTrue(self.employee.is_active)
        
        self.employee.status = EmploymentStatus.TERMINATED
        self.employee.save()
        
        self.assertFalse(self.employee.is_active)
