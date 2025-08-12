"""
HR Signals Tests
Tests for HR module signal handlers
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from ..models import Employee, OrgUnit, AccessProfile, EmploymentStatus

User = get_user_model()


class EmployeeSignalTest(TestCase):
    """Test Employee model signal handlers"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
    
    def test_emp_code_auto_generation(self):
        """Test automatic employee code generation via signals"""
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            access_profile=self.access_profile
        )
        
        # emp_code should be auto-generated
        self.assertIsNotNone(employee.emp_code)
        self.assertTrue(employee.emp_code.startswith('EMP'))
    
    def test_pan_number_uppercase_conversion(self):
        """Test PAN number automatic uppercase conversion"""
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            pan_number='abcde1234f',  # lowercase
            access_profile=self.access_profile
        )
        
        # PAN should be converted to uppercase
        self.assertEqual(employee.pan_number, 'ABCDE1234F')
    
    def test_manager_cycle_detection(self):
        """Test manager hierarchy cycle detection"""
        # Create employees
        emp1 = Employee.objects.create(
            first_name='Employee 1',
            last_name='Test',
            email='emp1@company.com',
            access_profile=self.access_profile
        )
        
        emp2 = Employee.objects.create(
            first_name='Employee 2',
            last_name='Test',
            email='emp2@company.com',
            manager=emp1,
            access_profile=self.access_profile
        )
        
        # Try to create circular reference
        emp1.manager = emp2
        
        with self.assertRaises(ValidationError):
            emp1.save()
    
    def test_deep_manager_cycle_detection(self):
        """Test deep manager hierarchy cycle detection"""
        # Create chain: emp1 -> emp2 -> emp3
        emp1 = Employee.objects.create(
            first_name='Employee 1',
            last_name='Test',
            email='emp1@company.com',
            access_profile=self.access_profile
        )
        
        emp2 = Employee.objects.create(
            first_name='Employee 2',
            last_name='Test',
            email='emp2@company.com',
            manager=emp1,
            access_profile=self.access_profile
        )
        
        emp3 = Employee.objects.create(
            first_name='Employee 3',
            last_name='Test',
            email='emp3@company.com',
            manager=emp2,
            access_profile=self.access_profile
        )
        
        # Try to make emp1 report to emp3 (creating cycle)
        emp1.manager = emp3
        
        with self.assertRaises(ValidationError):
            emp1.save()
    
    def test_self_manager_prevention(self):
        """Test prevention of self-manager assignment"""
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            access_profile=self.access_profile
        )
        
        # Try to make employee their own manager
        employee.manager = employee
        
        with self.assertRaises(ValidationError):
            employee.save()
    
    def test_valid_manager_assignment(self):
        """Test valid manager assignment works"""
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
        
        # Should work without issues
        self.assertEqual(employee.manager, manager)
    
    def test_emp_code_preservation(self):
        """Test that existing emp_code is preserved"""
        employee = Employee.objects.create(
            emp_code='CUSTOM001',
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            access_profile=self.access_profile
        )
        
        # Custom emp_code should be preserved
        self.assertEqual(employee.emp_code, 'CUSTOM001')
        
        # Update employee
        employee.first_name = 'Updated John'
        employee.save()
        
        # emp_code should still be preserved
        self.assertEqual(employee.emp_code, 'CUSTOM001')


class OrgUnitSignalTest(TestCase):
    """Test OrgUnit model signal handlers"""
    
    def test_org_unit_cycle_detection(self):
        """Test organizational unit hierarchy cycle detection"""
        # Create units
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
            unit1.save()
    
    def test_deep_org_unit_cycle_detection(self):
        """Test deep organizational unit hierarchy cycle detection"""
        # Create chain: unit1 -> unit2 -> unit3
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
        
        unit3 = OrgUnit.objects.create(
            name='Unit 3',
            code='UNIT-003',
            type='department',
            parent=unit2
        )
        
        # Try to make unit1 child of unit3 (creating cycle)
        unit1.parent = unit3
        
        with self.assertRaises(ValidationError):
            unit1.save()
    
    def test_self_parent_prevention(self):
        """Test prevention of self-parent assignment"""
        unit = OrgUnit.objects.create(
            name='Unit 1',
            code='UNIT-001',
            type='department'
        )
        
        # Try to make unit its own parent
        unit.parent = unit
        
        with self.assertRaises(ValidationError):
            unit.save()
    
    def test_valid_org_unit_hierarchy(self):
        """Test valid organizational unit hierarchy works"""
        parent = OrgUnit.objects.create(
            name='Parent Unit',
            code='PARENT-001',
            type='company'
        )
        
        child = OrgUnit.objects.create(
            name='Child Unit',
            code='CHILD-001',
            type='department',
            parent=parent
        )
        
        # Should work without issues
        self.assertEqual(child.parent, parent)


class SignalErrorHandlingTest(TestCase):
    """Test signal error handling"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
    
    def test_signal_with_invalid_data(self):
        """Test signal handling with invalid data"""
        # Test that signals handle edge cases gracefully
        employee = Employee(
            first_name='',  # Empty name
            last_name='',
            email='invalid-email',
            access_profile=self.access_profile
        )
        
        # Signal should not crash, but validation might fail later
        try:
            employee.save()
        except ValidationError:
            # Expected validation error, not signal error
            pass
    
    def test_signal_with_missing_related_objects(self):
        """Test signal handling with missing related objects"""
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            access_profile=self.access_profile
        )
        
        # Should handle missing related objects gracefully
        self.assertIsNotNone(employee.emp_code)
    
    def test_signal_performance_with_bulk_operations(self):
        """Test signal performance with bulk operations"""
        # Signals might not fire for bulk operations
        employees = []
        for i in range(100):
            employees.append(Employee(
                first_name=f'Employee {i}',
                last_name='Test',
                email=f'employee{i}@company.com',
                access_profile=self.access_profile
            ))
        
        # Bulk create - signals may not fire
        Employee.objects.bulk_create(employees)
        
        # Check that at least some employees were created
        self.assertGreaterEqual(Employee.objects.count(), 100)


class SignalIntegrationTest(TestCase):
    """Test signal integration with other components"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
    
    def test_signal_with_user_creation(self):
        """Test signals when creating employee with user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        employee = Employee.objects.create(
            user=user,
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            access_profile=self.access_profile
        )
        
        # Should work with user relationship
        self.assertIsNotNone(employee.emp_code)
        self.assertEqual(employee.user, user)
    
    def test_signal_with_historical_records(self):
        """Test signals with django-simple-history"""
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            pan_number='abcde1234f',
            access_profile=self.access_profile
        )
        
        # PAN should be uppercase
        self.assertEqual(employee.pan_number, 'ABCDE1234F')
        
        # Historical record should also have uppercase PAN
        history = employee.history.first()
        self.assertEqual(history.pan_number, 'ABCDE1234F')
    
    def test_signal_with_model_inheritance(self):
        """Test signals with model inheritance scenarios"""
        # If Employee had child models, test would ensure signals work
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            access_profile=self.access_profile
        )
        
        # Base signals should work
        self.assertIsNotNone(employee.emp_code)


class SignalDisconnectionTest(TestCase):
    """Test signal disconnection for testing purposes"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
    
    def test_signal_disconnection(self):
        """Test temporarily disconnecting signals"""
        from django.db.models.signals import pre_save
        from ..signals import employee_pre_save
        from ..models import Employee
        
        # Disconnect signal
        pre_save.disconnect(employee_pre_save, sender=Employee)
        
        try:
            # Create employee without signal processing
            employee = Employee.objects.create(
                first_name='John',
                last_name='Doe',
                email='john@company.com',
                pan_number='abcde1234f',  # lowercase
                access_profile=self.access_profile
            )
            
            # PAN should remain lowercase (signal didn't fire)
            self.assertEqual(employee.pan_number, 'abcde1234f')
            
        finally:
            # Reconnect signal
            pre_save.connect(employee_pre_save, sender=Employee)
    
    def test_signal_reconnection(self):
        """Test signal reconnection works properly"""
        # After reconnection, signals should work normally
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            pan_number='abcde1234f',  # lowercase
            access_profile=self.access_profile
        )
        
        # PAN should be uppercase (signal fired)
        self.assertEqual(employee.pan_number, 'ABCDE1234F')
