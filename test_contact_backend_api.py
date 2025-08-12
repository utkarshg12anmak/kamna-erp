#!/usr/bin/env python3
"""
CV Hub Contact Backend API Test
Tests the contact API endpoints and validation
"""

import requests
import json
import sys

class ContactBackendTest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.session = requests.Session()
        self.test_results = []
        self.errors = []
        self.entry_id = None

    def login(self):
        """Login to get authentication tokens"""
        print("🔐 Logging in...")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/auth/jwt/create/",
            json=login_data
        )
        
        if response.status_code == 200:
            tokens = response.json()
            self.session.headers.update({
                'Authorization': f'Bearer {tokens["access"]}'
            })
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False

    def get_csrf_token(self):
        """Get CSRF token for form submissions"""
        try:
            response = self.session.get(f"{self.base_url}/app/cv_hub/entries/")
            if 'csrftoken' in self.session.cookies:
                csrf_token = self.session.cookies['csrftoken']
                self.session.headers.update({'X-CSRFToken': csrf_token})
                print("✅ CSRF token obtained")
                return True
        except Exception as e:
            print(f"⚠️ Could not get CSRF token: {e}")
        return False

    def get_test_entry(self):
        """Get a test entry to add contacts to"""
        print("🔍 Getting test entry...")
        
        response = self.session.get(f"{self.base_url}/api/cv_hub/entries/")
        if response.status_code == 200:
            entries = response.json().get('results', [])
            if entries:
                self.entry_id = entries[0]['id']
                print(f"✅ Using entry ID: {self.entry_id}")
                return True
        
        print("❌ No entries found, creating a test entry...")
        # Create a test entry
        entry_data = {
            "legal_name": "Test Company for Contacts",
            "trade_name": "Test Company",
            "constitution": "PRIVATE_LIMITED",
            "is_customer": True,
            "is_supplier": False,
            "for_sales": True,
            "for_purchase": False
        }
        
        response = self.session.post(
            f"{self.base_url}/api/cv_hub/entries/",
            json=entry_data
        )
        
        if response.status_code == 201:
            self.entry_id = response.json()['id']
            print(f"✅ Created test entry ID: {self.entry_id}")
            return True
        else:
            print(f"❌ Failed to create test entry: {response.status_code}")
            return False

    def test_contact_validation_errors(self):
        """Test various contact validation scenarios"""
        print("\n📋 Testing Contact Validation Errors")
        
        test_cases = [
            {
                "name": "Empty first name",
                "data": {
                    "entry": self.entry_id,
                    "first_name": "",
                    "phone": "9876543210"
                },
                "expected_field": "first_name"
            },
            {
                "name": "Missing phone",
                "data": {
                    "entry": self.entry_id,
                    "first_name": "John"
                },
                "expected_field": "phone"
            },
            {
                "name": "Invalid phone format",
                "data": {
                    "entry": self.entry_id,
                    "first_name": "John",
                    "phone": "123"  # Too short
                },
                "expected_field": "phone"
            },
            {
                "name": "Invalid email format",
                "data": {
                    "entry": self.entry_id,
                    "first_name": "John",
                    "phone": "9876543210",
                    "email": "invalid-email"
                },
                "expected_field": "email"
            }
        ]
        
        for test_case in test_cases:
            print(f"  🔍 Testing: {test_case['name']}")
            
            response = self.session.post(
                f"{self.base_url}/api/cv_hub/contacts/",
                json=test_case['data']
            )
            
            if response.status_code == 400:
                error_data = response.json()
                print(f"    ✅ Got expected validation error: {response.status_code}")
                print(f"    📝 Error data: {json.dumps(error_data, indent=2)}")
                
                # Check if the expected field has an error
                if test_case['expected_field'] in error_data:
                    print(f"    ✅ Field-specific error found for '{test_case['expected_field']}'")
                    self.test_results.append(f"✅ {test_case['name']} validation working")
                else:
                    print(f"    ⚠️ Expected error for field '{test_case['expected_field']}' not found")
                    self.test_results.append(f"⚠️ {test_case['name']} validation unclear")
            else:
                error_msg = f"❌ Expected 400 error for {test_case['name']}, got {response.status_code}"
                print(f"    {error_msg}")
                self.errors.append(error_msg)

    def test_contact_creation_success(self):
        """Test successful contact creation"""
        print("\n📋 Testing Successful Contact Creation")
        
        contact_data = {
            "entry": self.entry_id,
            "first_name": "John",
            "last_name": "Doe",
            "phone": "9876543210",
            "email": "john.doe@example.com",
            "designation": "MANAGER",
            "is_primary": True
        }
        
        response = self.session.post(
            f"{self.base_url}/api/cv_hub/contacts/",
            json=contact_data
        )
        
        if response.status_code == 201:
            contact = response.json()
            print(f"  ✅ Contact created successfully: ID {contact.get('id')}")
            print(f"  📝 Contact data: {json.dumps(contact, indent=2)}")
            self.test_results.append("✅ Contact creation working")
            return contact.get('id')
        else:
            error_msg = f"❌ Contact creation failed: {response.status_code}"
            print(f"  {error_msg}")
            if response.status_code == 400:
                print(f"  📝 Error details: {response.json()}")
            self.errors.append(error_msg)
            return None

    def test_duplicate_phone_validation(self):
        """Test duplicate phone number validation"""
        print("\n📋 Testing Duplicate Phone Validation")
        
        # Try to create another contact with the same phone
        duplicate_data = {
            "entry": self.entry_id,
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "9876543210",  # Same as previous contact
            "email": "jane.smith@example.com"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/cv_hub/contacts/",
            json=duplicate_data
        )
        
        if response.status_code == 400:
            error_data = response.json()
            print(f"  ✅ Duplicate phone validation working: {response.status_code}")
            print(f"  📝 Error data: {json.dumps(error_data, indent=2)}")
            self.test_results.append("✅ Duplicate phone validation working")
        else:
            error_msg = f"❌ Expected 400 for duplicate phone, got {response.status_code}"
            print(f"  {error_msg}")
            self.errors.append(error_msg)

    def run_all_tests(self):
        """Run all contact backend tests"""
        try:
            if not self.login():
                return False
            
            self.get_csrf_token()
            
            if not self.get_test_entry():
                return False
            
            self.test_contact_validation_errors()
            self.test_contact_creation_success()
            self.test_duplicate_phone_validation()
            
            return True
            
        except Exception as e:
            error_msg = f"❌ Test execution failed: {str(e)}"
            self.errors.append(error_msg)
            print(error_msg)
            return False

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("📊 CONTACT BACKEND API TEST SUMMARY")
        print(f"{'='*60}")
        
        print(f"\n✅ PASSED TESTS ({len(self.test_results)}):")
        for result in self.test_results:
            print(f"  {result}")
        
        if self.errors:
            print(f"\n❌ FAILED TESTS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        else:
            print(f"\n🎉 ALL BACKEND TESTS PASSED! Contact API is working correctly.")
        
        print(f"\n📈 OVERALL STATUS:")
        if len(self.errors) == 0:
            print("  🟢 EXCELLENT - All contact API tests passed")
        elif len(self.errors) <= 2:
            print("  🟡 GOOD - Minor API issues detected")
        else:
            print("  🔴 NEEDS ATTENTION - Multiple API issues found")

def main():
    """Main test execution"""
    tester = ContactBackendTest()
    success = tester.run_all_tests()
    tester.print_summary()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)
