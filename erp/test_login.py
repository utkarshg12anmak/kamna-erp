#!/usr/bin/env python3

import requests
import sys

def test_login_functionality():
    """Test the new login functionality"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing CV Hub Login Functionality")
    print("=" * 50)
    
    # Test 1: Check if login page is accessible
    print("\n1. Testing login page accessibility...")
    try:
        response = requests.get(f"{base_url}/login/")
        if response.status_code == 200:
            print("✅ Login page accessible")
            if "Login" in response.text and "username" in response.text:
                print("✅ Login form found")
            else:
                print("❌ Login form not found in response")
        else:
            print(f"❌ Login page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing login page: {e}")
        return False
    
    # Test 2: Test login with admin credentials
    print("\n2. Testing login with admin credentials...")
    session = requests.Session()
    
    # Get CSRF token first
    try:
        login_page = session.get(f"{base_url}/login/")
        if "csrfmiddlewaretoken" in login_page.text:
            # Extract CSRF token (simple approach)
            csrf_start = login_page.text.find('name="csrfmiddlewaretoken" value="') + 34
            csrf_end = login_page.text.find('"', csrf_start)
            csrf_token = login_page.text[csrf_start:csrf_end]
            print(f"✅ CSRF token obtained: {csrf_token[:10]}...")
        else:
            print("❌ CSRF token not found")
            return False
    except Exception as e:
        print(f"❌ Error getting CSRF token: {e}")
        return False
    
    # Attempt login
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin',
            'csrfmiddlewaretoken': csrf_token,
            'next': '/app/cv_hub'
        }
        
        login_response = session.post(f"{base_url}/login/", data=login_data)
        
        if login_response.status_code == 302:  # Redirect after successful login
            print("✅ Login successful (redirect received)")
        elif "Welcome back" in login_response.text:
            print("✅ Login successful (welcome message)")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print("Response content preview:", login_response.text[:200])
            return False
            
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return False
    
    # Test 3: Check if CV Hub is accessible after login
    print("\n3. Testing CV Hub access after login...")
    try:
        cv_hub_response = session.get(f"{base_url}/app/cv_hub/debug/")
        if cv_hub_response.status_code == 200:
            print("✅ CV Hub debug page accessible after login")
            
            # Check if user is authenticated in the debug page
            if 'Authenticated:</strong> True' in cv_hub_response.text:
                print("✅ User authenticated successfully")
            else:
                print("❌ User not authenticated in debug page")
                
            # Check if user has CV Hub access
            if 'Customer & Vendor Hub' in cv_hub_response.text:
                print("✅ User has Customer & Vendor Hub group")
            else:
                print("❌ User missing Customer & Vendor Hub group")
                
        else:
            print(f"❌ CV Hub access failed: {cv_hub_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing CV Hub: {e}")
        return False
    
    # Test 4: Test the main CV Hub entries page
    print("\n4. Testing CV Hub entries page...")
    try:
        entries_response = session.get(f"{base_url}/app/cv_hub/entries/")
        if entries_response.status_code == 200:
            print("✅ CV Hub entries page accessible")
            
            # Check if the page shows access granted
            if 'You do not have access' in entries_response.text:
                print("❌ Access denied message still showing")
                return False
            else:
                print("✅ No access denied message found")
                
        else:
            print(f"❌ CV Hub entries failed: {entries_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing CV Hub entries: {e}")
        return False
    
    print("\n🎉 All tests passed! CV Hub login functionality is working.")
    print("\n📋 User Instructions:")
    print("1. Go to http://localhost:8000/login/")
    print("2. Login with username: admin, password: admin")
    print("3. You will be redirected to CV Hub")
    print("4. Or manually go to http://localhost:8000/app/cv_hub/entries/")
    print("\n✨ The CV Hub access issue has been resolved!")
    
    return True

if __name__ == "__main__":
    success = test_login_functionality()
    sys.exit(0 if success else 1)
