#!/usr/bin/env python3
"""
Test Position API Access with Session Authentication
"""

import requests
import sys
import os

def test_position_api():
    """Test position API access with session authentication"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Position API with Session Authentication")
    print("=" * 60)
    
    # Create a session
    session = requests.Session()
    
    # Step 1: Get login page and CSRF token
    print("\n1. Getting CSRF token...")
    try:
        login_page = session.get(f"{base_url}/login/")
        if login_page.status_code != 200:
            print(f"❌ Login page not accessible: {login_page.status_code}")
            return False
            
        # Extract CSRF token
        if "csrfmiddlewaretoken" in login_page.text:
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
    
    # Step 2: Login with admin credentials
    print("\n2. Logging in with admin credentials...")
    try:
        login_data = {
            'username': 'admin',
            'password': 'admin',
            'csrfmiddlewaretoken': csrf_token,
        }
        
        login_response = session.post(f"{base_url}/login/", data=login_data)
        
        if login_response.status_code == 200 or login_response.status_code == 302:
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 3: Test positions API
    print("\n3. Testing positions API...")
    try:
        positions_response = session.get(f"{base_url}/api/hr/positions/")
        
        print(f"Positions API Status: {positions_response.status_code}")
        
        if positions_response.status_code == 200:
            positions_data = positions_response.json()
            positions_list = positions_data.get('results', positions_data)
            
            print(f"✅ Positions API accessible")
            print(f"   Found {len(positions_list)} positions:")
            
            for position in positions_list[:5]:  # Show first 5
                print(f"   - {position.get('title', 'Unknown')} (ID: {position.get('id', 'N/A')})")
                
            if len(positions_list) > 5:
                print(f"   ... and {len(positions_list) - 5} more")
                
            return True
            
        else:
            print(f"❌ Positions API failed: {positions_response.status_code}")
            print(f"   Response: {positions_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Positions API error: {e}")
        return False

if __name__ == "__main__":
    success = test_position_api()
    sys.exit(0 if success else 1)
