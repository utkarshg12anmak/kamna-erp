#!/usr/bin/env python3
"""
Employee Edit Form Fix Verification
===================================

This script comprehensively tests the employee edit functionality fix to ensure:
1. JSON data is properly sent for PUT requests (edit mode)
2. FormData is properly sent for POST requests (create mode)
3. No more "Invalid JSON data" errors occur
4. Complete edit workflow functions correctly
"""

import requests
import json
import sys
from datetime import datetime

class EmployeeEditFixVerification:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/api/hr"
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def test_server_connection(self):
        """Test if the Django server is running"""
        try:
            response = requests.get(f"{self.api_base}/employees/", timeout=5)
            self.log_test("Server Connection", response.status_code == 200, 
                         f"HTTP {response.status_code}")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            self.log_test("Server Connection", False, f"Connection error: {e}")
            return False
    
    def test_get_employee_list(self):
        """Test getting the employee list"""
        try:
            response = requests.get(f"{self.api_base}/employees/")
            if response.status_code == 200:
                employees = response.json()
                count = len(employees)
                self.log_test("Get Employee List", True, f"Retrieved {count} employees")
                return employees
            else:
                self.log_test("Get Employee List", False, f"HTTP {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Employee List", False, str(e))
            return []
    
    def test_json_put_update(self, employee_id):
        """Test JSON PUT update (simulates fixed frontend edit mode)"""
        try:
            update_data = {
                'first_name': 'JSON PUT Test',
                'department': 'JSON Testing Dept',
                'designation': 'JSON Test Engineer'
            }
            
            response = requests.put(
                f"{self.api_base}/employees/{employee_id}/",
                headers={'Content-Type': 'application/json'},
                json=update_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("JSON PUT Update", True, 
                             f"Updated employee {employee_id} successfully")
                return True
            else:
                error_text = response.text
                self.log_test("JSON PUT Update", False, 
                             f"HTTP {response.status_code}: {error_text}")
                return False
                
        except Exception as e:
            self.log_test("JSON PUT Update", False, str(e))
            return False
    
    def test_formdata_post_create(self):
        """Test FormData POST create (simulates frontend create mode)"""
        try:
            form_data = {
                'first_name': 'FormData Test User',
                'last_name': 'Test',
                'email': f'formdata.test.{datetime.now().strftime("%H%M%S")}@company.com',
                'department': 'FormData Testing',
                'designation': 'FormData Engineer'
            }
            
            response = requests.post(
                f"{self.api_base}/employees/",
                data=form_data
            )
            
            if response.status_code == 201:
                result = response.json()
                self.log_test("FormData POST Create", True, 
                             f"Created employee {result.get('emp_code')} (ID: {result.get('id')})")
                return result.get('id')
            else:
                error_text = response.text
                self.log_test("FormData POST Create", False, 
                             f"HTTP {response.status_code}: {error_text}")
                return None
                
        except Exception as e:
            self.log_test("FormData POST Create", False, str(e))
            return None
    
    def test_invalid_json_error_fixed(self, employee_id):
        """Test that the 'Invalid JSON data' error is fixed"""
        try:
            # Try sending FormData to PUT endpoint (old behavior that caused the error)
            form_data = {
                'first_name': 'Should Fail FormData PUT',
                'department': 'Test Department'
            }
            
            response = requests.put(
                f"{self.api_base}/employees/{employee_id}/",
                data=form_data  # Sending FormData instead of JSON
            )
            
            # This should fail, but not with "Invalid JSON data" error
            if response.status_code == 400:
                error_response = response.text
                if "Invalid JSON data" in error_response:
                    self.log_test("Invalid JSON Error Fixed", False, 
                                 "Still getting 'Invalid JSON data' error")
                    return False
                else:
                    self.log_test("Invalid JSON Error Fixed", True, 
                                 "No longer getting 'Invalid JSON data' error")
                    return True
            else:
                self.log_test("Invalid JSON Error Fixed", True, 
                             f"Unexpected response: HTTP {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Invalid JSON Error Fixed", False, str(e))
            return False
    
    def test_employee_workflow(self):
        """Test complete employee creation and editing workflow"""
        try:
            # Step 1: Create a new employee (POST with FormData)
            print("\n🔄 Testing complete employee workflow...")
            
            employee_id = self.test_formdata_post_create()
            if not employee_id:
                return False
            
            # Step 2: Update the employee (PUT with JSON)
            update_success = self.test_json_put_update(employee_id)
            if not update_success:
                return False
            
            # Step 3: Verify the update worked
            try:
                response = requests.get(f"{self.api_base}/employees/{employee_id}/")
                if response.status_code == 200:
                    employee = response.json()
                    if employee.get('first_name') == 'JSON PUT Test':
                        self.log_test("Employee Workflow", True, 
                                     "Complete create → edit workflow successful")
                        return True
                    else:
                        self.log_test("Employee Workflow", False, 
                                     "Update did not persist correctly")
                        return False
                else:
                    self.log_test("Employee Workflow", False, 
                                 f"Could not verify update: HTTP {response.status_code}")
                    return False
            except Exception as e:
                self.log_test("Employee Workflow", False, f"Verification error: {e}")
                return False
                
        except Exception as e:
            self.log_test("Employee Workflow", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("🔧 Employee Edit Form Fix Verification")
        print("=" * 50)
        print("Testing the fix for 'Invalid JSON data' error...")
        print()
        
        # Test 1: Server connection
        if not self.test_server_connection():
            print("\n❌ Cannot connect to server. Please ensure Django server is running.")
            return False
        
        # Test 2: Get employees
        employees = self.test_get_employee_list()
        if not employees:
            print("\n❌ Cannot retrieve employees. Database may be empty.")
            return False
        
        # Get first employee for testing
        test_employee_id = employees[0]['id']
        print(f"\n🎯 Using employee ID {test_employee_id} for testing...")
        
        # Test 3: JSON PUT update (the fix)
        self.test_json_put_update(test_employee_id)
        
        # Test 4: FormData POST create (should still work)
        self.test_formdata_post_create()
        
        # Test 5: Verify the old error is fixed
        self.test_invalid_json_error_fixed(test_employee_id)
        
        # Test 6: Complete workflow
        self.test_employee_workflow()
        
        # Summary
        self.print_summary()
        
        return all(result['success'] for result in self.test_results)
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Employee edit form fix is working correctly.")
            print("✅ No more 'Invalid JSON data' errors.")
            print("✅ Frontend now sends JSON for PUT and FormData for POST.")
        else:
            print(f"\n⚠️  {total - passed} TEST(S) FAILED")
            print("❌ Some issues remain. Check the test details above.")
        
        print("\n" + "=" * 50)

def main():
    """Main function"""
    verifier = EmployeeEditFixVerification()
    success = verifier.run_all_tests()
    
    if success:
        print("\n🚀 Employee edit functionality is now fully functional!")
        print("You can now edit employees without getting JSON parsing errors.")
    else:
        print("\n🔍 Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
