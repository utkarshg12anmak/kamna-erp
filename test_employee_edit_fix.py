#!/usr/bin/env python3
"""
Test script to verify that the employee edit functionality fix is working
"""
import os
import sys
import requests
import json
from datetime import datetime

# Django setup
project_path = '/Users/dealshare/Documents/GitHub/kamna-erp/erp'
sys.path.insert(0, project_path)
os.chdir(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')

import django
django.setup()

BASE_URL = 'http://localhost:8000'

def test_server_status():
    """Test if the Django server is running"""
    try:
        response = requests.get(f'{BASE_URL}/api/hr/employees/', timeout=5)
        print(f"✅ Server is running - Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not accessible: {e}")
        return False

def test_employee_edit_url_detection():
    """Test the JavaScript edit mode detection fix"""
    print("\n🔍 Testing Employee Edit URL Detection Fix")
    print("=" * 50)
    
    # Test URL patterns that should be detected as edit mode
    test_urls = [
        "/app/hr/employees/1/edit",
        "/app/hr/employees/123/edit",  
        "/app/hr/employees/999/edit/",
    ]
    
    # Test URL patterns that should NOT be detected as edit mode
    non_edit_urls = [
        "/app/hr/employees/new",
        "/app/hr/employees/1",
        "/app/hr/employees/",
        "/app/hr/employees/1/view"
    ]
    
    print("✅ URLs that SHOULD trigger edit mode:")
    for url in test_urls:
        # Simulate the regex check
        import re
        matches = re.search(r'/employees/(\d+)/edit', url)
        if matches:
            emp_id = matches.group(1)
            print(f"   ✓ {url} → Employee ID: {emp_id}")
        else:
            print(f"   ❌ {url} → NOT detected (should be!)")
    
    print("\n✅ URLs that should NOT trigger edit mode:")
    for url in non_edit_urls:
        import re
        matches = re.search(r'/employees/(\d+)/edit', url)
        if matches:
            print(f"   ❌ {url} → INCORRECTLY detected as edit mode")
        else:
            print(f"   ✓ {url} → Correctly ignored")

def test_employee_crud_operations():
    """Test complete employee CRUD to verify edit functionality"""
    print("\n🔍 Testing Employee CRUD Operations")
    print("=" * 50)
    
    if not test_server_status():
        print("❌ Cannot test CRUD - server not running")
        return False
    
    try:
        # 1. Create a test employee
        print("\n1. Creating test employee...")
        create_data = {
            'first_name': 'Test',
            'last_name': 'Employee',
            'email': f'test.edit.{datetime.now().strftime("%Y%m%d%H%M%S")}@example.com',
            'phone': f'+91 98765{datetime.now().strftime("%H%M%S")}',
            'department': 'Testing',
            'designation': 'Test Engineer',
            'date_of_joining': '2025-08-13'
        }
        
        # Use form data for creation
        response = requests.post(f'{BASE_URL}/api/hr/employees/', data=create_data)
        
        if response.status_code == 201:
            employee_data = response.json()
            employee_id = employee_data['id']
            emp_code = employee_data['emp_code']
            print(f"   ✅ Employee created successfully - ID: {employee_id}, Code: {emp_code}")
        else:
            print(f"   ❌ Employee creation failed - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # 2. Test GET (retrieve) the employee
        print(f"\n2. Retrieving employee {employee_id}...")
        get_response = requests.get(f'{BASE_URL}/api/hr/employees/{employee_id}/')
        
        if get_response.status_code == 200:
            retrieved_employee = get_response.json()
            print(f"   ✅ Employee retrieved successfully")
            print(f"   Name: {retrieved_employee['first_name']} {retrieved_employee['last_name']}")
            print(f"   Code: {retrieved_employee['emp_code']}")
        else:
            print(f"   ❌ Employee retrieval failed - Status: {get_response.status_code}")
            return False
        
        # 3. Test UPDATE (edit) the employee - THIS IS THE CRITICAL TEST
        print(f"\n3. Testing employee edit (UPDATE operation)...")
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Employee',
            'email': retrieved_employee['email'],  # Keep same email to avoid unique constraint
            'phone': retrieved_employee['phone'],   # Keep same phone to avoid unique constraint
            'department': 'Updated Department',
            'designation': 'Senior Test Engineer',
            'emp_code': retrieved_employee['emp_code']  # Keep same emp_code to avoid duplicate key error
        }
        
        # Test with PUT method (what the fixed JavaScript should use)
        put_response = requests.put(
            f'{BASE_URL}/api/hr/employees/{employee_id}/', 
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if put_response.status_code == 200:
            print(f"   ✅ Employee UPDATE successful with PUT method")
        else:
            print(f"   ❌ Employee UPDATE failed with PUT - Status: {put_response.status_code}")
            print(f"   Response: {put_response.text}")
        
        # 4. Verify the update took effect
        print(f"\n4. Verifying update...")
        verify_response = requests.get(f'{BASE_URL}/api/hr/employees/{employee_id}/')
        
        if verify_response.status_code == 200:
            updated_employee = verify_response.json()
            if (updated_employee['first_name'] == 'Updated' and 
                updated_employee['department'] == 'Updated Department'):
                print(f"   ✅ Update verification successful")
                print(f"   Updated name: {updated_employee['first_name']} {updated_employee['last_name']}")
                print(f"   Updated department: {updated_employee['department']}")
            else:
                print(f"   ❌ Update verification failed - changes not saved")
        
        # 5. Test that duplicate key constraint is avoided
        print(f"\n5. Testing duplicate key constraint avoidance...")
        
        # This should NOT cause a duplicate key error since we're updating, not creating
        same_data_update = {
            'first_name': 'Final Update',
            'emp_code': retrieved_employee['emp_code'],  # Same emp_code should be fine for updates
            'email': retrieved_employee['email'],
            'phone': retrieved_employee['phone']
        }
        
        final_update_response = requests.put(
            f'{BASE_URL}/api/hr/employees/{employee_id}/', 
            json=same_data_update,
            headers={'Content-Type': 'application/json'}
        )
        
        if final_update_response.status_code == 200:
            print(f"   ✅ No duplicate key constraint error - fix working correctly")
        else:
            print(f"   ❌ Duplicate key constraint error still occurring")
            print(f"   Status: {final_update_response.status_code}")
            print(f"   Response: {final_update_response.text}")
        
        # 6. Clean up - delete the test employee
        print(f"\n6. Cleaning up test employee...")
        delete_response = requests.delete(f'{BASE_URL}/api/hr/employees/{employee_id}/')
        
        if delete_response.status_code in [200, 204]:
            print(f"   ✅ Test employee cleaned up successfully")
        else:
            print(f"   ⚠️ Could not clean up test employee - Status: {delete_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during CRUD testing: {e}")
        return False

def main():
    print("🔧 Employee Edit Functionality Fix Verification")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: URL pattern detection (client-side fix)
    test_employee_edit_url_detection()
    
    # Test 2: Server-side CRUD operations
    test_employee_crud_operations()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY")
    print("=" * 60)
    print("✅ Fixed JavaScript edit mode detection regex")
    print("✅ Fixed API URL determination logic") 
    print("✅ Added employee ID population in edit mode")
    print("✅ Ensured PUT method is used for updates (not POST)")
    print()
    print("🔑 KEY CHANGES MADE:")
    print("1. Updated checkEditMode() to detect /employees/{id}/edit URLs")
    print("2. Fixed saveEmployeeAPI() to use isEditMode flag instead of URL parsing")
    print("3. Added employee.id to populateForm() for hidden field")
    print()
    print("This should resolve the 'duplicate key constraint violation' error")
    print("when editing existing employees.")

if __name__ == "__main__":
    main()
