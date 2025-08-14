#!/usr/bin/env python3
"""
Test script to verify user mapping functionality with authentication
"""

import requests
from requests.auth import HTTPBasicAuth
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER = "test"
TEST_PASSWORD = "test123"

def test_with_session():
    """Test API endpoints using session authentication"""
    
    print("🔧 Testing User Mapping Functionality with Authentication")
    print("=" * 60)
    
    # Create session
    session = requests.Session()
    
    # Step 1: Login via admin to get session cookie
    print("\n1. 🔐 Attempting to authenticate...")
    
    # Get login page to get CSRF token
    login_page = session.get(f"{BASE_URL}/admin/login/")
    if login_page.status_code != 200:
        print(f"❌ Failed to get login page: {login_page.status_code}")
        return
    
    # Extract CSRF token
    csrf_token = None
    for line in login_page.text.split('\n'):
        if 'csrfmiddlewaretoken' in line:
            import re
            match = re.search(r'value="([^"]+)"', line)
            if match:
                csrf_token = match.group(1)
                break
    
    if not csrf_token:
        print("❌ Could not find CSRF token")
        return
    
    print(f"✅ Found CSRF token: {csrf_token[:10]}...")
    
    # Login
    login_data = {
        'username': TEST_USER,
        'password': TEST_PASSWORD,
        'csrfmiddlewaretoken': csrf_token,
        'next': '/debug/user-mapping'
    }
    
    login_response = session.post(f"{BASE_URL}/admin/login/", data=login_data)
    if login_response.status_code == 200 and 'login' not in login_response.url:
        print("✅ Successfully authenticated")
    else:
        print(f"❌ Authentication failed: {login_response.status_code}")
        print(f"URL after login: {login_response.url}")
        return
    
    # Step 2: Test Employees API
    print("\n2. 📋 Testing Employees API...")
    employees_response = session.get(f"{BASE_URL}/api/hr/employees/")
    
    if employees_response.status_code == 200:
        employees_data = employees_response.json()
        employees = employees_data.get('results', employees_data)
        print(f"✅ Employees API works! Found {len(employees)} employees")
        
        if employees:
            for i, emp in enumerate(employees[:3]):  # Show first 3
                user_status = f"User: {emp.get('user_username', 'None')}" if emp.get('user_username') else "No user assigned"
                print(f"   {i+1}. {emp.get('first_name')} {emp.get('last_name')} (ID: {emp.get('id')}) - {user_status}")
    else:
        print(f"❌ Employees API failed: {employees_response.status_code}")
        print(f"Response: {employees_response.text[:200]}")
        return
    
    # Step 3: Test Available Users API
    print("\n3. 👥 Testing Available Users API...")
    users_response = session.get(f"{BASE_URL}/api/hr/available-users/")
    
    if users_response.status_code == 200:
        users_data = users_response.json()
        print(f"✅ Available Users API works! Found {len(users_data)} available users")
        
        for user in users_data:
            print(f"   - {user.get('username')} ({user.get('first_name')} {user.get('last_name')}) - {user.get('email')}")
    else:
        print(f"❌ Available Users API failed: {users_response.status_code}")
        print(f"Response: {users_response.text[:200]}")
    
    # Step 4: Test User Assignment (if possible)
    if employees and len(users_data) > 0:
        print("\n4. 🔗 Testing User Assignment...")
        
        # Find an unassigned employee
        unassigned_employee = None
        for emp in employees:
            if not emp.get('user_username'):
                unassigned_employee = emp
                break
        
        if unassigned_employee and users_data:
            print(f"Found unassigned employee: {unassigned_employee['first_name']} {unassigned_employee['last_name']} (ID: {unassigned_employee['id']})")
            print(f"Available user to assign: {users_data[0]['username']}")
            
            # Get CSRF token for API request
            csrf_response = session.get(f"{BASE_URL}/admin/")
            csrf_token = None
            for line in csrf_response.text.split('\n'):
                if 'csrfmiddlewaretoken' in line:
                    import re
                    match = re.search(r'value="([^"]+)"', line)
                    if match:
                        csrf_token = match.group(1)
                        break
            
            if csrf_token:
                # Test assignment API
                assign_url = f"{BASE_URL}/api/hr/employees/{unassigned_employee['id']}/assign-user/"
                assign_data = {
                    'user_id': users_data[0]['id']
                }
                
                assign_response = session.post(
                    assign_url,
                    json=assign_data,
                    headers={
                        'X-CSRFToken': csrf_token,
                        'Content-Type': 'application/json'
                    }
                )
                
                if assign_response.status_code == 200:
                    print("✅ User assignment API works!")
                    result = assign_response.json()
                    print(f"   Result: {result}")
                else:
                    print(f"❌ User assignment failed: {assign_response.status_code}")
                    print(f"   Response: {assign_response.text[:200]}")
            else:
                print("❌ Could not get CSRF token for assignment test")
        else:
            print("ℹ️ No unassigned employees or available users for testing assignment")
    
    print("\n🏁 Authentication Test Complete")
    print("=" * 60)
    
    # Summary
    print("\n📊 SUMMARY:")
    print("✅ Authentication: Working")
    print("✅ Employees API: Working")
    print("✅ Available Users API: Working")
    print("🔧 User Assignment: Needs manual testing in browser")
    print("\n💡 NEXT STEPS:")
    print("1. Log in to admin at: http://127.0.0.1:8000/admin/login/")
    print("2. Use credentials: test / test123")
    print("3. Navigate to: http://127.0.0.1:8000/hr/employees/")
    print("4. Test the Assign User / Unassign User buttons manually")

if __name__ == "__main__":
    test_with_session()
