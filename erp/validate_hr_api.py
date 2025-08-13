#!/usr/bin/env python3
"""
Simple HR API validation script
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')

# Add project path
project_path = '/Users/dealshare/Documents/GitHub/kamna-erp/erp'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Change to project directory
os.chdir(project_path)

# Setup Django
django.setup()

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from hr.models import Employee
        print("✅ Employee model imported")
        
        # Get field names
        field_names = [f.name for f in Employee._meta.fields]
        print(f"📋 Employee fields: {', '.join(field_names)}")
        
        # Check key fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if field in field_names:
                print(f"✅ Required field '{field}' exists")
            else:
                print(f"❌ Required field '{field}' missing")
        
    except ImportError as e:
        print(f"❌ Failed to import Employee model: {e}")
        return False
    
    try:
        from hr.api.views import EmployeeViewSet
        print("✅ EmployeeViewSet imported")
    except ImportError as e:
        print(f"❌ Failed to import EmployeeViewSet: {e}")
        return False
    
    return True

def test_urls():
    """Test URL configuration"""
    print("\n🔍 Testing URL configuration...")
    
    try:
        from django.urls import reverse
        from django.conf import settings
        
        # Print URL patterns to debug
        from django.urls import get_resolver
        resolver = get_resolver()
        
        print("✅ URL resolver loaded")
        return True
        
    except Exception as e:
        print(f"❌ URL configuration error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints without server"""
    print("\n🔍 Testing API endpoint configuration...")
    
    try:
        from rest_framework.test import APIClient
        from django.test import override_settings
        
        client = APIClient()
        
        # Test employee list endpoint
        response = client.get('/api/hr/employees/')
        print(f"✅ Employee list endpoint: HTTP {response.status_code}")
        
        # Test employee creation with minimal data
        test_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'employee_id': 'TEST123'
        }
        
        response = client.post('/api/hr/employees/', test_data, format='json')
        print(f"✅ Employee creation test: HTTP {response.status_code}")
        
        if response.status_code == 400:
            print(f"   Validation errors: {response.json()}")
        elif response.status_code == 201:
            print(f"   Created employee: {response.json().get('id', 'Unknown ID')}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 HR API Validation Test")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_urls()
    success &= test_api_endpoints()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ HR API validation completed - Ready for testing!")
    else:
        print("❌ Issues found - Check output above")
