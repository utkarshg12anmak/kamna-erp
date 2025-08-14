#!/usr/bin/env python3
"""
Test script for user-employee mapping functionality
"""
import sys
import os
import django

# Add the erp directory to Python path
sys.path.append('/Users/dealshare/Documents/GitHub/kamna-erp/erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.contrib.auth import get_user_model
from hr.models import Employee
from hr.api.serializers import AvailableUserSerializer, EmployeeListSerializer

User = get_user_model()

def test_user_mapping_functionality():
    print("🔍 Testing User-Employee Mapping Functionality")
    print("=" * 50)
    
    # 1. Test available users query
    print("\n1. Testing Available Users Query:")
    assigned_user_ids = Employee.objects.values_list('user_id', flat=True).exclude(user_id__isnull=True)
    available_users = User.objects.exclude(id__in=assigned_user_ids)
    
    print(f"   Total users: {User.objects.count()}")
    print(f"   Assigned user IDs: {list(assigned_user_ids)}")
    print(f"   Available users: {available_users.count()}")
    
    for user in available_users:
        print(f"     - {user.username} ({user.first_name} {user.last_name})")
    
    # 2. Test AvailableUserSerializer
    print("\n2. Testing AvailableUserSerializer:")
    serializer = AvailableUserSerializer(available_users, many=True)
    print(f"   Serialized data: {serializer.data}")
    
    # 3. Test EmployeeListSerializer with user info
    print("\n3. Testing EmployeeListSerializer with User Info:")
    employees = Employee.objects.all()[:3]  # Test with first 3 employees
    serializer = EmployeeListSerializer(employees, many=True)
    
    for emp_data in serializer.data:
        user_info = f"User: {emp_data['user_username']}" if emp_data['user_username'] else "No user"
        print(f"   - {emp_data['first_name']} {emp_data['last_name']} - {user_info}")
    
    # 4. Test user assignment simulation
    print("\n4. Testing User Assignment Simulation:")
    if available_users.exists() and employees.exists():
        test_employee = employees.first()
        test_user = available_users.first()
        
        print(f"   Before assignment:")
        print(f"     Employee: {test_employee.first_name} {test_employee.last_name}")
        print(f"     User assigned: {test_employee.user}")
        
        # Simulate assignment
        test_employee.user = test_user
        test_employee.save()
        
        print(f"   After assignment:")
        print(f"     Employee: {test_employee.first_name} {test_employee.last_name}")
        print(f"     User assigned: {test_employee.user.username}")
        
        # Test updated serialization
        updated_serializer = EmployeeListSerializer(test_employee)
        print(f"     Serialized user info: {updated_serializer.data['user_username']}")
        
        # Clean up - remove assignment
        test_employee.user = None
        test_employee.save()
        print(f"   Assignment removed for cleanup")
    
    print("\n✅ User mapping functionality test completed!")

if __name__ == "__main__":
    test_user_mapping_functionality()
