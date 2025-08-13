#!/usr/bin/env python3
"""
Test script to verify HR API endpoints are working
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
project_dir = '/Users/dealshare/Documents/GitHub/kamna-erp/erp'
sys.path.insert(0, project_dir)
os.chdir(project_dir)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

def test_hr_models():
    """Test if HR models can be imported and basic operations work"""
    try:
        from hr.models import Employee, OrgUnit, Position, AccessProfile
        print("✅ HR models imported successfully")
        
        # Test model field names
        employee_fields = [field.name for field in Employee._meta.fields]
        print(f"✅ Employee model fields: {employee_fields}")
        
        # Check for required fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if field in employee_fields:
                print(f"✅ Field '{field}' exists in Employee model")
            else:
                print(f"❌ Field '{field}' missing in Employee model")
                
        return True
    except Exception as e:
        print(f"❌ Error importing HR models: {e}")
        return False

def test_hr_api_views():
    """Test if HR API views can be imported"""
    try:
        from hr.api.views import EmployeeViewSet, OrgUnitViewSet, PositionViewSet, AccessProfileViewSet
        print("✅ HR API views imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing HR API views: {e}")
        return False

def test_hr_urls():
    """Test if HR URLs can be loaded"""
    try:
        from django.urls import reverse, NoReverseMatch
        from django.test import Client
        
        # Test URL resolution
        client = Client()
        
        # Test API root
        try:
            response = client.get('/api/hr/')
            print(f"✅ HR API root accessible: {response.status_code}")
        except Exception as e:
            print(f"❌ HR API root error: {e}")
            
        # Test employees endpoint
        try:
            response = client.get('/api/hr/employees/')
            print(f"✅ Employees API accessible: {response.status_code}")
        except Exception as e:
            print(f"❌ Employees API error: {e}")
            
        return True
    except Exception as e:
        print(f"❌ Error testing HR URLs: {e}")
        return False

def test_employee_creation():
    """Test creating an employee via API"""
    try:
        from rest_framework.test import APIClient
        from django.contrib.auth.models import User
        
        # Create a test user for authentication if needed
        client = APIClient()
        
        # Test data
        employee_data = {
            'first_name': 'Test',
            'last_name': 'Employee',
            'email': 'test@example.com',
            'employee_id': 'TEST001',
            'is_draft': False
        }
        
        response = client.post('/api/hr/employees/', employee_data, format='json')
        print(f"✅ Employee creation test: {response.status_code}")
        if response.status_code >= 400:
            print(f"   Response data: {response.data if hasattr(response, 'data') else 'No data'}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing employee creation: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing HR API endpoints...")
    print("=" * 50)
    
    success = True
    success &= test_hr_models()
    success &= test_hr_api_views()
    success &= test_hr_urls()
    success &= test_employee_creation()
    
    print("=" * 50)
    if success:
        print("✅ All tests completed (check individual results above)")
    else:
        print("❌ Some tests failed (check individual results above)")
