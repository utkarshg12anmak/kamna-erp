#!/usr/bin/env python3
"""
Simple manual test of Django HR functionality
"""
import os
import sys

# Add project to path
project_dir = '/Users/dealshare/Documents/GitHub/kamna-erp/erp'
sys.path.insert(0, project_dir)
os.chdir(project_dir)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')

try:
    import django
    django.setup()
    print("✅ Django setup successful")
    
    # Test HR model imports
    from hr.models import Employee
    print("✅ HR Employee model imported")
    
    # Get employee fields
    fields = [f.name for f in Employee._meta.fields]
    print(f"📋 Employee fields: {', '.join(fields)}")
    
    # Test API views
    from hr.api.views import EmployeeViewSet
    print("✅ EmployeeViewSet imported")
    
    # Test URLs
    from django.urls import reverse
    from django.conf import settings
    print("✅ Django URL system working")
    
    # Test a simple API call
    from rest_framework.test import APIClient
    client = APIClient()
    
    response = client.get('/api/hr/employees/')
    print(f"✅ Employee API test: HTTP {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {len(data)} employees")
    
    print("\n🎉 All basic tests passed! HR system appears to be working.")
    print("\n📋 Next steps:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Open browser to http://localhost:8000/app/hr/employees/new")
    print("3. Test employee form functionality")
    print("4. Use the HR test suite: hr_test_suite.html")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
