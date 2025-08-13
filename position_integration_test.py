#!/usr/bin/env python3
"""
Complete Position Dropdown Integration Test
Tests the entire flow from login to position dropdown in employee form
"""

import time
import requests
import sys
import subprocess
import threading
import signal
import os
from urllib.parse import urljoin

class PositionDropdownTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.server_process = None
        self.session = requests.Session()
        
    def start_server(self):
        """Start Django development server"""
        print("🚀 Starting Django development server...")
        
        # Change to the Django project directory
        django_dir = "/Users/dealshare/Documents/GitHub/kamna-erp/erp"
        
        try:
            self.server_process = subprocess.Popen(
                ["python", "manage.py", "runserver", "8000"],
                cwd=django_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for server to start
            time.sleep(3)
            
            # Check if server is running
            try:
                response = requests.get(self.base_url, timeout=5)
                print("✅ Django server started successfully")
                return True
            except requests.exceptions.ConnectionError:
                print("❌ Django server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop Django development server"""
        if self.server_process:
            print("🛑 Stopping Django server...")
            self.server_process.terminate()
            self.server_process.wait()
    
    def login(self):
        """Login to Django admin"""
        print("🔐 Logging in as admin...")
        
        try:
            # Get login page and CSRF token
            login_page = self.session.get(f"{self.base_url}/login/")
            if login_page.status_code != 200:
                print(f"❌ Login page not accessible: {login_page.status_code}")
                return False
                
            # Extract CSRF token
            if "csrfmiddlewaretoken" in login_page.text:
                csrf_start = login_page.text.find('name="csrfmiddlewaretoken" value="') + 34
                csrf_end = login_page.text.find('"', csrf_start)
                csrf_token = login_page.text[csrf_start:csrf_end]
                print(f"   CSRF token obtained: {csrf_token[:10]}...")
            else:
                print("❌ CSRF token not found")
                return False
            
            # Login
            login_data = {
                'username': 'admin',
                'password': 'admin123',
                'csrfmiddlewaretoken': csrf_token,
            }
            
            login_response = self.session.post(f"{self.base_url}/login/", data=login_data)
            
            if login_response.status_code in [200, 302]:
                print("✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test all HR API endpoints"""
        print("🧪 Testing HR API endpoints...")
        
        endpoints = [
            ("/api/hr/positions/", "Positions"),
            ("/api/hr/employees/", "Employees"), 
            ("/api/hr/org-units/", "Org Units"),
            ("/api/hr/access-profiles/", "Access Profiles"),
        ]
        
        all_passed = True
        
        for endpoint, name in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('results', data) if isinstance(data, dict) else data
                    print(f"   ✅ {name}: {len(items)} items")
                    
                    # Show a few examples for positions
                    if endpoint == "/api/hr/positions/" and len(items) > 0:
                        for item in items[:3]:
                            print(f"      - {item.get('title', 'Unknown')} (ID: {item.get('id', 'N/A')})")
                        if len(items) > 3:
                            print(f"      ... and {len(items) - 3} more")
                            
                else:
                    print(f"   ❌ {name}: HTTP {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ {name}: Error - {e}")
                all_passed = False
        
        return all_passed
    
    def test_employee_form_access(self):
        """Test employee form page access"""
        print("📋 Testing employee form access...")
        
        try:
            # Test new employee form
            response = self.session.get(f"{self.base_url}/app/hr/employees/new")
            
            if response.status_code == 200:
                print("   ✅ Employee form accessible")
                
                # Check if form contains position dropdown
                if 'id="position"' in response.text:
                    print("   ✅ Position dropdown found in form")
                else:
                    print("   ❌ Position dropdown not found in form")
                    return False
                    
                # Check if loadPositions function is present
                if 'loadPositions' in response.text:
                    print("   ✅ loadPositions function found")
                else:
                    print("   ❌ loadPositions function not found")
                    return False
                    
                return True
            else:
                print(f"   ❌ Employee form not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Employee form access error: {e}")
            return False
    
    def run_complete_test(self):
        """Run the complete test suite"""
        print("🎯 Position Dropdown Integration Test")
        print("=" * 50)
        
        success = True
        
        try:
            # Start server
            if not self.start_server():
                return False
            
            # Login
            if not self.login():
                success = False
            
            # Test API endpoints
            if success and not self.test_api_endpoints():
                success = False
            
            # Test employee form
            if success and not self.test_employee_form_access():
                success = False
            
            print("\n" + "=" * 50)
            if success:
                print("🎉 ALL TESTS PASSED!")
                print("\nThe position dropdown should now work correctly:")
                print("1. ✅ Session authentication is working")
                print("2. ✅ Position API returns data")
                print("3. ✅ Employee form loads correctly")
                print("4. ✅ loadPositions function is present")
                print("\n📝 Next steps:")
                print("   - Visit: http://localhost:8000/app/hr/employees/new")
                print("   - The position dropdown should populate automatically")
                print("   - Check browser console for loading logs")
            else:
                print("❌ SOME TESTS FAILED!")
                print("Please check the errors above and fix them.")
            
        finally:
            self.stop_server()
        
        return success

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Interrupted by user")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    test = PositionDropdownTest()
    success = test.run_complete_test()
    sys.exit(0 if success else 1)
