#!/usr/bin/env python3
"""
Simple test for user mapping API endpoints
"""
import sys
import os
import django

# Add the erp directory to Python path
sys.path.append('/Users/dealshare/Documents/GitHub/kamna-erp/erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from hr.models import Employee
import json

User = get_user_model()

def test_api_endpoints():
    print("🔍 Testing User Mapping API Endpoints")
    print("=" * 40)
    
    # Create a test client
    client = Client()
    
    # Login as admin (if needed for authentication)
    admin_user = User.objects.filter(username='admin').first()
    if admin_user:
        client.force_login(admin_user)
        print("✅ Logged in as admin")
    
    # 1. Test available users endpoint
    print("\n1. Testing /api/hr/available-users/ endpoint:")
    try:
        response = client.get('/api/hr/available-users/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Available users: {len(data)}")
            for user in data:
                print(f"     - {user['username']} ({user['first_name']} {user['last_name']})")
        else:
            print(f"   Error: {response.content}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 2. Test employee list endpoint
    print("\n2. Testing /api/hr/employees/ endpoint:")
    try:
        response = client.get('/api/hr/employees/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Employees: {len(data)}")
            for emp in data[:3]:  # Show first 3
                user_info = emp.get('user_username', 'No user')
                print(f"     - {emp['first_name']} {emp['last_name']} - User: {user_info}")
        else:
            print(f"   Error: {response.content}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 3. Test user assignment
    print("\n3. Testing user assignment:")
    try:
        # Get first employee and first available user
        employees = Employee.objects.all()
        users = User.objects.all()
        
        if employees.exists() and users.exists():
            test_employee = employees.first()
            test_user = users.first()
            
            # Test assignment
            assignment_data = {'user_id': test_user.id}
            response = client.post(
                f'/api/hr/employees/{test_employee.id}/assign-user/',
                data=json.dumps(assignment_data),
                content_type='application/json'
            )
            
            print(f"   Assignment Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Success: {result.get('message', 'User assigned')}")
                
                # Test unassignment
                unassign_response = client.post(f'/api/hr/employees/{test_employee.id}/unassign-user/')
                print(f"   Unassignment Status: {unassign_response.status_code}")
                if unassign_response.status_code == 200:
                    unassign_result = unassign_response.json()
                    print(f"   Success: {unassign_result.get('message', 'User unassigned')}")
            else:
                print(f"   Assignment Error: {response.content}")
        else:
            print("   No employees or users available for testing")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n✅ API endpoint testing completed!")

if __name__ == "__main__":
    test_api_endpoints()
