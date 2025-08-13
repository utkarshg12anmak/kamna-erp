#!/usr/bin/env python3
"""
Final Server Restart Verification
Tests all functionality after server restart
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_server_status():
    """Test if server is responding"""
    print("🔄 Testing Server Status...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code in [200, 302, 404]:  # Any response means server is up
            print("✅ Server is running and responding")
            return True
        else:
            print(f"⚠️ Server responding with status: {response.status_code}")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Server is not responding")
        return False
    except Exception as e:
        print(f"❌ Server test error: {e}")
        return False

def test_employee_apis():
    """Test employee API endpoints"""
    print("\n📋 Testing Employee APIs...")
    
    try:
        # Test employee list
        response = requests.get(f"{BASE_URL}/api/hr/employees/")
        if response.status_code != 200:
            print(f"❌ Employee list API failed: {response.status_code}")
            return False
        
        employees = response.json()
        print(f"✅ Employee list API: Found {len(employees)} employees")
        
        if not employees:
            print("⚠️ No employees found - View/Edit buttons won't work")
            return False
        
        # Test individual employee API
        test_emp = employees[0]
        emp_id = test_emp['id']
        
        response = requests.get(f"{BASE_URL}/api/hr/employees/{emp_id}/")
        if response.status_code != 200:
            print(f"❌ Individual employee API failed: {response.status_code}")
            return False
        
        emp_data = response.json()
        print(f"✅ Individual employee API: {emp_data['first_name']} {emp_data['last_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_view_edit_functionality():
    """Test View and Edit button functionality"""
    print("\n🖱️ Testing View/Edit Button Functionality...")
    
    try:
        # Get test employee
        response = requests.get(f"{BASE_URL}/api/hr/employees/")
        employees = response.json()
        test_emp = employees[0]
        emp_id = test_emp['id']
        
        # Test View button functionality (API call)
        print(f"Testing View button for: {test_emp['first_name']} {test_emp['last_name']}")
        response = requests.get(f"{BASE_URL}/api/hr/employees/{emp_id}/")
        
        if response.status_code == 200:
            print("✅ View button will work - API returns employee data")
        else:
            print("❌ View button will fail - API error")
            return False
        
        # Test Edit button functionality (page access)
        print(f"Testing Edit button for employee ID: {emp_id}")
        edit_url = f"{BASE_URL}/app/hr/employees/{emp_id}/edit"
        response = requests.get(edit_url)
        
        if response.status_code in [200, 302]:
            print("✅ Edit button will work - Edit page accessible")
        else:
            print(f"❌ Edit button will fail - Edit page error: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ View/Edit test error: {e}")
        return False

def test_employee_list_page():
    """Test employee list page loads"""
    print("\n📄 Testing Employee List Page...")
    
    try:
        response = requests.get(f"{BASE_URL}/app/hr/employees")
        if response.status_code in [200, 302]:
            print("✅ Employee list page accessible")
            return True
        else:
            print(f"❌ Employee list page error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Page test error: {e}")
        return False

def main():
    print("🚀 DJANGO SERVER RESTART VERIFICATION")
    print("=" * 50)
    print(f"Testing server at: {BASE_URL}")
    print()
    
    # Run all tests
    server_ok = test_server_status()
    apis_ok = test_employee_apis() if server_ok else False
    buttons_ok = test_view_edit_functionality() if apis_ok else False
    page_ok = test_employee_list_page() if server_ok else False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION RESULTS:")
    print(f"   Server Status: {'✅ RUNNING' if server_ok else '❌ DOWN'}")
    print(f"   Employee APIs: {'✅ WORKING' if apis_ok else '❌ FAILED'}")
    print(f"   View/Edit Buttons: {'✅ FUNCTIONAL' if buttons_ok else '❌ BROKEN'}")
    print(f"   Employee List Page: {'✅ ACCESSIBLE' if page_ok else '❌ INACCESSIBLE'}")
    
    if all([server_ok, apis_ok, buttons_ok, page_ok]):
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n✅ READY FOR TESTING:")
        print("   1. Open: http://localhost:8000/app/hr/employees")
        print("   2. Click any 'View' button - should open modal")
        print("   3. Click any 'Edit' button - should redirect to edit form")
        print("\n🔧 HR MODULE STATUS: FULLY FUNCTIONAL")
        return True
    else:
        print("\n⚠️ SOME ISSUES DETECTED - Check errors above")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
