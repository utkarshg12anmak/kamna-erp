#!/usr/bin/env python3
"""
Test script to verify View and Edit button functionality
"""

import requests
import sys
import json

BASE_URL = "http://localhost:8000"

def test_individual_employee_api():
    """Test the individual employee API endpoint"""
    print("🧪 Testing Individual Employee API Endpoint...")
    
    try:
        # First, get all employees to find an employee ID
        response = requests.get(f"{BASE_URL}/api/hr/employees/")
        
        if response.status_code != 200:
            print(f"❌ Failed to get employees list: {response.status_code}")
            return False
        
        employees = response.json()
        
        if not employees:
            print("❌ No employees found in database")
            return False
        
        # Test with the first employee
        test_employee = employees[0]
        employee_id = test_employee['id']
        
        print(f"📋 Testing with Employee ID: {employee_id} ({test_employee['first_name']} {test_employee['last_name']})")
        
        # Test individual employee GET endpoint
        response = requests.get(f"{BASE_URL}/api/hr/employees/{employee_id}/")
        
        if response.status_code == 200:
            employee_data = response.json()
            print(f"✅ Individual employee API working!")
            print(f"   Employee: {employee_data['first_name']} {employee_data['last_name']}")
            print(f"   Code: {employee_data['emp_code']}")
            print(f"   Email: {employee_data['email']}")
            return True
        else:
            print(f"❌ Individual employee API failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_view_button_flow():
    """Simulate the View button click flow"""
    print("\n🖱️ Testing View Button Flow...")
    
    try:
        # Get employees list
        response = requests.get(f"{BASE_URL}/api/hr/employees/")
        employees = response.json()
        
        if not employees:
            print("❌ No employees for testing")
            return False
        
        employee_id = employees[0]['id']
        
        # Simulate viewEmployee() function call
        response = requests.get(f"{BASE_URL}/api/hr/employees/{employee_id}/")
        
        if response.status_code == 200:
            employee_data = response.json()
            print(f"✅ View button would work correctly!")
            print(f"   Modal would show: {employee_data['first_name']} {employee_data['last_name']}")
            return True
        else:
            print(f"❌ View button would fail: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ View button test error: {e}")
        return False

def test_edit_button_flow():
    """Test the Edit button redirect"""
    print("\n✏️ Testing Edit Button Flow...")
    
    try:
        # Get employees list
        response = requests.get(f"{BASE_URL}/api/hr/employees/")
        employees = response.json()
        
        if not employees:
            print("❌ No employees for testing")
            return False
        
        employee_id = employees[0]['id']
        edit_url = f"{BASE_URL}/app/hr/employees/{employee_id}/edit"
        
        # Test if the edit page loads (just check if it doesn't return 404)
        response = requests.get(edit_url)
        
        if response.status_code in [200, 302]:  # 200 OK or 302 redirect
            print(f"✅ Edit button would work correctly!")
            print(f"   Would redirect to: {edit_url}")
            return True
        else:
            print(f"❌ Edit button would fail: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Edit button test error: {e}")
        return False

def main():
    print("🔧 Testing View and Edit Button Functionality")
    print("=" * 50)
    
    # Test individual employee API
    api_test = test_individual_employee_api()
    
    # Test View button flow
    view_test = test_view_button_flow()
    
    # Test Edit button flow  
    edit_test = test_edit_button_flow()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   Individual Employee API: {'✅ PASS' if api_test else '❌ FAIL'}")
    print(f"   View Button Flow: {'✅ PASS' if view_test else '❌ FAIL'}")
    print(f"   Edit Button Flow: {'✅ PASS' if edit_test else '❌ FAIL'}")
    
    if all([api_test, view_test, edit_test]):
        print("\n🎉 ALL TESTS PASSED! View and Edit buttons should work correctly.")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
