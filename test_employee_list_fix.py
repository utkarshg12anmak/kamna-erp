#!/usr/bin/env python3
"""
Employee List Display Test
Tests if the employee list page loads correctly with the serializer fix
"""

import os
import sys
import django
import json

# Setup Django
django_path = "/Users/dealshare/Documents/GitHub/kamna-erp/erp"
sys.path.insert(0, django_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_employee_list():
    print("🧪 Employee List Display Test")
    print("=" * 40)
    
    User = get_user_model()
    admin = User.objects.filter(is_superuser=True).first()
    
    if not admin:
        print("❌ No admin user found")
        return False
    
    client = Client()
    logged_in = client.login(username=admin.username, password='admin123')
    
    if not logged_in:
        print("❌ Login failed")
        return False
        
    print("✅ Login successful")
    
    # Test API endpoint
    print("\n📡 Testing Employee API...")
    api_response = client.get('/api/hr/employees/')
    
    if api_response.status_code == 200:
        api_data = api_response.json()
        employees = api_data.get('results', [])
        print(f"✅ API working: {len(employees)} employees returned")
        
        if employees:
            # Check required fields
            first_emp = employees[0]
            required_fields = ['first_name', 'last_name', 'emp_code', 'email', 'status']
            missing_fields = [field for field in required_fields if field not in first_emp]
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                return False
            else:
                print("✅ All required fields present")
                
            # Show sample employees
            print("\n👥 Sample employees:")
            for emp in employees[:3]:
                name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
                status = emp.get('status', 'Unknown')
                emp_code = emp.get('emp_code', 'N/A')
                print(f"   - {name} ({emp_code}) - {status}")
                
        else:
            print("⚠️  No employees returned from API")
            
    else:
        print(f"❌ API failed: {api_response.status_code}")
        return False
    
    # Test employee list page
    print("\n📋 Testing Employee List Page...")
    page_response = client.get('/app/hr/employees')
    
    if page_response.status_code == 200:
        print("✅ Employee list page accessible")
        
        page_content = page_response.content.decode()
        
        # Check for essential elements
        checks = [
            ('Employee table', 'id="employeesTable"'),
            ('Search field', 'id="q"'),
            ('Status filters', 'data-status="ACTIVE"'),
            ('JavaScript loading', 'loadEmployees'),
        ]
        
        all_passed = True
        for check_name, check_pattern in checks:
            if check_pattern in page_content:
                print(f"   ✅ {check_name} found")
            else:
                print(f"   ❌ {check_name} missing")
                all_passed = False
                
        if all_passed:
            print("✅ All page elements present")
        else:
            print("❌ Some page elements missing")
            return False
            
    else:
        print(f"❌ Employee list page failed: {page_response.status_code}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 Employee List Test PASSED!")
    print("\n📋 Summary:")
    print(f"   • API returns {len(employees)} employees")
    print("   • All required fields present (first_name, last_name, etc.)")
    print("   • Employee list page loads correctly")
    print("   • All UI elements present")
    
    print("\n🚀 Next Steps:")
    print("   1. Start server: python manage.py runserver")
    print("   2. Visit: http://localhost:8000/app/hr/employees")
    print("   3. Employees should now display correctly!")
    
    return True

if __name__ == "__main__":
    success = test_employee_list()
    sys.exit(0 if success else 1)
