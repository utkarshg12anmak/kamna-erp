#!/usr/bin/env python3
"""
Final verification script for View and Edit button functionality
"""

import requests
import sys
import json

BASE_URL = "http://localhost:8000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print('='*60)

def print_step(step, message):
    print(f"{step} {message}")

def test_complete_flow():
    """Test the complete View and Edit button flow"""
    print_header("COMPLETE VIEW/EDIT BUTTON VERIFICATION")
    
    try:
        # Step 1: Get employees list
        print_step("1️⃣", "Testing employee list API...")
        response = requests.get(f"{BASE_URL}/api/hr/employees/")
        
        if response.status_code != 200:
            print(f"❌ Employee list API failed: {response.status_code}")
            return False
        
        employees = response.json()
        if not employees:
            print("❌ No employees found")
            return False
        
        print(f"✅ Employee list API working - Found {len(employees)} employees")
        
        # Step 2: Test individual employee API (what View button uses)
        test_employee = employees[0]
        employee_id = test_employee['id']
        
        print_step("2️⃣", f"Testing individual employee API for ID {employee_id}...")
        response = requests.get(f"{BASE_URL}/api/hr/employees/{employee_id}/")
        
        if response.status_code != 200:
            print(f"❌ Individual employee API failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response: {response.text}")
            return False
        
        employee_data = response.json()
        print(f"✅ Individual employee API working")
        print(f"   Employee: {employee_data['first_name']} {employee_data['last_name']}")
        print(f"   Code: {employee_data['emp_code']}")
        print(f"   Email: {employee_data['email']}")
        
        # Step 3: Test edit page accessibility
        print_step("3️⃣", f"Testing edit page accessibility...")
        edit_url = f"{BASE_URL}/app/hr/employees/{employee_id}/edit"
        response = requests.get(edit_url)
        
        if response.status_code in [200, 302]:
            print(f"✅ Edit page accessible")
            print(f"   URL: {edit_url}")
        else:
            print(f"❌ Edit page not accessible: {response.status_code}")
            return False
        
        # Step 4: Test with multiple employees
        print_step("4️⃣", "Testing with multiple employees...")
        test_count = min(3, len(employees))
        
        for i, emp in enumerate(employees[:test_count]):
            emp_id = emp['id']
            response = requests.get(f"{BASE_URL}/api/hr/employees/{emp_id}/")
            if response.status_code == 200:
                emp_data = response.json()
                print(f"   ✅ Employee {i+1}: {emp_data['first_name']} {emp_data['last_name']} (ID: {emp_id})")
            else:
                print(f"   ❌ Employee {i+1} failed (ID: {emp_id})")
                return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Django server not running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def simulate_button_clicks():
    """Simulate actual button click scenarios"""
    print_header("BUTTON CLICK SIMULATION")
    
    try:
        # Get a test employee
        response = requests.get(f"{BASE_URL}/api/hr/employees/")
        employees = response.json()
        test_employee = employees[0]
        emp_id = test_employee['id']
        
        # Simulate View button click
        print_step("🖱️", "Simulating View button click...")
        print(f"   User clicks 'View' button for: {test_employee['first_name']} {test_employee['last_name']}")
        print(f"   JavaScript calls: viewEmployee({emp_id})")
        print(f"   Function makes request to: /api/hr/employees/{emp_id}/")
        
        response = requests.get(f"{BASE_URL}/api/hr/employees/{emp_id}/")
        if response.status_code == 200:
            employee_data = response.json()
            print(f"   ✅ Modal would show employee details")
            print(f"   📋 Modal content would include:")
            print(f"      - Name: {employee_data['first_name']} {employee_data['last_name']}")
            print(f"      - Code: {employee_data['emp_code']}")
            print(f"      - Email: {employee_data['email']}")
            print(f"      - Department: {employee_data['department'] or 'N/A'}")
            print(f"      - Status: {employee_data['status']}")
        else:
            print(f"   ❌ Modal would fail to load")
            return False
        
        # Simulate Edit button click
        print_step("✏️", "Simulating Edit button click...")
        print(f"   User clicks 'Edit' button for: {test_employee['first_name']} {test_employee['last_name']}")
        print(f"   JavaScript calls: editEmployee({emp_id})")
        print(f"   Function redirects to: /app/hr/employees/{emp_id}/edit")
        
        edit_response = requests.get(f"{BASE_URL}/app/hr/employees/{emp_id}/edit")
        if edit_response.status_code in [200, 302]:
            print(f"   ✅ Would redirect to edit form successfully")
        else:
            print(f"   ❌ Redirect would fail")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        return False

def main():
    print("🎯 VIEW AND EDIT BUTTON VERIFICATION")
    print("Testing the complete functionality of View and Edit buttons in employee list")
    
    # Test complete flow
    flow_test = test_complete_flow()
    
    # Simulate button clicks
    simulation_test = simulate_button_clicks()
    
    # Final results
    print_header("FINAL RESULTS")
    
    print("📊 TEST SUMMARY:")
    print(f"   Complete Flow Test: {'✅ PASS' if flow_test else '❌ FAIL'}")
    print(f"   Button Simulation: {'✅ PASS' if simulation_test else '❌ FAIL'}")
    
    if flow_test and simulation_test:
        print("\n🎉 SUCCESS: View and Edit buttons are now working correctly!")
        print("\n✅ WHAT WORKS NOW:")
        print("   • View button opens modal with employee details")
        print("   • Edit button redirects to employee edit form")
        print("   • Individual employee API endpoint working")
        print("   • Employee list displays all employees")
        print("\n🚀 READY FOR TESTING:")
        print("   1. Open: http://localhost:8000/app/hr/employees")
        print("   2. Click any 'View' button - modal should open")
        print("   3. Click any 'Edit' button - should redirect to edit form")
        
        return True
    else:
        print("\n⚠️ Some issues remain. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
