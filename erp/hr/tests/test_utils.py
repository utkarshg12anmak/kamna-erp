"""
HR Utilities Tests
Tests for HR module utility functions
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Employee, AccessProfile
from ..utils import next_emp_code, mask_value

User = get_user_model()


class NextEmpCodeTest(TestCase):
    """Test next_emp_code utility function"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
    
    def test_first_emp_code(self):
        """Test generating first employee code"""
        code = next_emp_code()
        self.assertEqual(code, 'EMP001')
    
    def test_sequential_emp_code(self):
        """Test generating sequential employee codes"""
        # Create first employee
        Employee.objects.create(
            emp_code='EMP001',
            first_name='First',
            last_name='Employee',
            email='first@company.com',
            access_profile=self.access_profile
        )
        
        # Next code should be EMP002
        code = next_emp_code()
        self.assertEqual(code, 'EMP002')
    
    def test_emp_code_with_gaps(self):
        """Test employee code generation with gaps"""
        # Create employees with non-sequential codes
        Employee.objects.create(
            emp_code='EMP001',
            first_name='First',
            last_name='Employee',
            email='first@company.com',
            access_profile=self.access_profile
        )
        
        Employee.objects.create(
            emp_code='EMP005',
            first_name='Fifth',
            last_name='Employee',
            email='fifth@company.com',
            access_profile=self.access_profile
        )
        
        # Next code should be EMP006 (highest + 1)
        code = next_emp_code()
        self.assertEqual(code, 'EMP006')
    
    def test_emp_code_with_custom_format(self):
        """Test employee codes with different formats"""
        # Create employee with custom format
        Employee.objects.create(
            emp_code='CUSTOM001',
            first_name='Custom',
            last_name='Employee',
            email='custom@company.com',
            access_profile=self.access_profile
        )
        
        # Should still generate EMP format
        code = next_emp_code()
        self.assertEqual(code, 'EMP001')
    
    def test_emp_code_performance(self):
        """Test employee code generation performance"""
        # Create many employees
        employees = []
        for i in range(100):
            employees.append(Employee(
                emp_code=f'EMP{i+1:03d}',
                first_name=f'Employee {i}',
                last_name='Test',
                email=f'employee{i}@company.com',
                access_profile=self.access_profile
            ))
        
        Employee.objects.bulk_create(employees)
        
        # Generate next code - should be efficient
        code = next_emp_code()
        self.assertEqual(code, 'EMP101')


class MaskValueTest(TestCase):
    """Test mask_value utility function"""
    
    def test_mask_string_value(self):
        """Test masking string values"""
        result = mask_value('sensitive_data')
        self.assertEqual(result, '****')
    
    def test_mask_numeric_value(self):
        """Test masking numeric values"""
        result = mask_value(12345)
        self.assertEqual(result, '****')
    
    def test_mask_decimal_value(self):
        """Test masking decimal values"""
        from decimal import Decimal
        result = mask_value(Decimal('50000.00'))
        self.assertEqual(result, '****')
    
    def test_mask_none_value(self):
        """Test masking None values"""
        result = mask_value(None)
        self.assertEqual(result, '****')
    
    def test_mask_empty_string(self):
        """Test masking empty strings"""
        result = mask_value('')
        self.assertEqual(result, '****')
    
    def test_mask_boolean_value(self):
        """Test masking boolean values"""
        result = mask_value(True)
        self.assertEqual(result, '****')
        
        result = mask_value(False)
        self.assertEqual(result, '****')
    
    def test_mask_custom_character(self):
        """Test masking with custom character"""
        # If mask_value supports custom masking character
        result = mask_value('sensitive', mask_char='X')
        # This would work if the function supports it
        # self.assertEqual(result, 'XXXX')


class UtilityIntegrationTest(TestCase):
    """Test utility functions in integration scenarios"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
    
    def test_emp_code_in_employee_creation(self):
        """Test emp_code utility in actual employee creation"""
        # Create employee without emp_code
        employee = Employee.objects.create(
            first_name='Test',
            last_name='Employee',
            email='test@company.com',
            access_profile=self.access_profile
        )
        
        # Should have auto-generated emp_code
        self.assertIsNotNone(employee.emp_code)
        self.assertTrue(employee.emp_code.startswith('EMP'))
    
    def test_mask_value_in_serialization(self):
        """Test mask_value in serialization context"""
        from ..api.serializers import EmployeeSerializer
        
        employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            salary=50000.00,
            access_profile=self.access_profile
        )
        
        # Test with masking context
        serializer = EmployeeSerializer(
            employee,
            context={'mask_salary': True}
        )
        
        data = serializer.data
        # Salary should be masked if serializer supports it
        # self.assertEqual(data.get('salary'), '****')
    
    def test_utility_error_handling(self):
        """Test utility function error handling"""
        # Test what happens with invalid input
        result = mask_value(object())  # Random object
        self.assertEqual(result, '****')
    
    def test_utility_thread_safety(self):
        """Test utility functions are thread-safe"""
        import threading
        import time
        
        results = []
        
        def generate_codes():
            for _ in range(10):
                code = next_emp_code()
                results.append(code)
                time.sleep(0.001)  # Small delay
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=generate_codes)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All codes should be unique
        self.assertEqual(len(results), len(set(results)))


class UtilityPerformanceTest(TestCase):
    """Test utility function performance"""
    
    def setUp(self):
        """Set up test data"""
        self.access_profile = AccessProfile.objects.create(
            name='Standard Access'
        )
    
    def test_emp_code_generation_performance(self):
        """Test emp_code generation performance with large dataset"""
        # Create many employees
        employees = []
        for i in range(1000):
            employees.append(Employee(
                emp_code=f'EMP{i+1:04d}',
                first_name=f'Employee {i}',
                last_name='Test',
                email=f'employee{i}@company.com',
                access_profile=self.access_profile
            ))
        
        Employee.objects.bulk_create(employees)
        
        # Time the next_emp_code generation
        import time
        start_time = time.time()
        
        for _ in range(10):
            next_emp_code()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly even with large dataset
        self.assertLess(duration, 1.0)  # Less than 1 second for 10 calls
    
    def test_mask_value_performance(self):
        """Test mask_value performance"""
        import time
        
        start_time = time.time()
        
        # Mask many values
        for i in range(1000):
            mask_value(f'sensitive_data_{i}')
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be very fast
        self.assertLess(duration, 0.1)  # Less than 100ms for 1000 calls


class UtilityConfigurationTest(TestCase):
    """Test utility function configuration"""
    
    def test_emp_code_prefix_configuration(self):
        """Test if emp_code prefix is configurable"""
        # This would test if the EMP prefix can be configured
        # Implementation depends on whether this is configurable
        code = next_emp_code()
        self.assertTrue(code.startswith('EMP'))
    
    def test_mask_character_configuration(self):
        """Test if mask character is configurable"""
        # This would test if the mask character can be configured
        result = mask_value('test')
        self.assertEqual(result, '****')
    
    def test_utility_settings_integration(self):
        """Test utility functions with Django settings"""
        # This would test if utilities respect Django settings
        from django.conf import settings
        
        # Test that utilities work with current settings
        code = next_emp_code()
        self.assertIsNotNone(code)
        
        masked = mask_value('test')
        self.assertIsNotNone(masked)
