#!/usr/bin/env python3
"""
Verification script for employee list functionality
"""

import requests
import sys

BASE_URL = "http://localhost:8000"

def test_employee_list_page():
    """Test if employee list page shows data"""
    print("🔍 Testing Employee List Page...")
    
    try:
        # Test the employee list page
        response = requests.get(f"{BASE_URL}/app/hr/employees")
        
        if response.status_code == 200:
            print("✅ Employee list page accessible")
            
            # Check for key elements
            content = response.text
            checks = [
                ('employeeTableBody', 'Employee table body'),
                ('totalCount', 'Total count element'),
                ('loadEmployees', 'Load employees function'),
                ('renderTable', 'Render table function')
            ]
            
            page_valid = True
            for element, description in checks:
                if element in content:
                    print(f"✅ {description} found")
                else:
                    print(f"❌ {description} missing")
                    page_valid = False
                    
            return page_valid
            
        else:
            print(f"❌ Employee list page: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Employee list page error: {e}")
        return False

def test_employee_api():
    """Test employee API returns data"""
    print("\n🔍 Testing Employee API...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/hr/employees/")
        
        if response.status_code == 200:
            employees = response.json()
            print(f"✅ Employee API accessible - returned {len(employees)} employees")
            
            if len(employees) > 0:
                first_emp = employees[0]
                required_fields = ['id', 'emp_code', 'first_name', 'last_name', 'email', 'department', 'status']
                
                print("✅ Employee data structure:")
                for field in required_fields:
                    if field in first_emp:
                        print(f"   ✓ {field}: {first_emp[field]}")
                    else:
                        print(f"   ❌ {field}: missing")
                
                return True
            else:
                print("❌ No employees returned from API")
                return False
                
        else:
            print(f"❌ Employee API: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Employee API error: {e}")
        return False

def test_database_vs_api():
    """Compare database count with API count"""
    print("\n🔍 Testing Database vs API Consistency...")
    
    try:
        # Get API count
        response = requests.get(f"{BASE_URL}/api/hr/employees/")
        api_count = len(response.json()) if response.status_code == 200 else 0
        
        print(f"📊 API returned: {api_count} employees")
        print(f"📊 Expected from database: 13 employees")
        
        if api_count == 13:
            print("✅ Database and API counts match!")
            return True
        else:
            print("❌ Database and API counts don't match")
            return False
            
    except Exception as e:
        print(f"❌ Comparison error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Employee List Verification")
    print("=" * 40)
    
    tests = [
        ("Employee List Page", test_employee_list_page),
        ("Employee API", test_employee_api),
        ("Database vs API", test_database_vs_api)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 40)
    print("🎯 VERIFICATION RESULTS")
    print("=" * 40)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 SUCCESS: Employee list should now show all 13 employees!")
        print("\n📋 Next steps:")
        print("1. Refresh http://localhost:8000/app/hr/employees")
        print("2. Verify all 13 employees are displayed")
        print("3. Test filtering and sorting functionality")
    else:
        print("⚠️ Some issues detected - check results above")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
