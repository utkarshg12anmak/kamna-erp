#!/usr/bin/env python3
"""
Comprehensive HR Module Final Verification
Tests all HR module functionality to ensure everything is working correctly
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(endpoint, description, expected_status=200):
    """Test an endpoint and return result"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"🔍 Testing: {endpoint}")
        print(f"   Description: {description}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == expected_status:
            print(f"✅ SUCCESS: HTTP {response.status_code}")
            
            # Try to parse JSON if possible
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    data = response.json()
                    if isinstance(data, list):
                        print(f"📊 Returned: {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"📊 Keys: {list(data.keys())}")
                    return True, data
                else:
                    print(f"📄 HTML Response: {len(response.text)} characters")
                    return True, response.text
            except:
                print(f"📄 Non-JSON response")
                return True, response.text
        else:
            print(f"❌ FAILED: HTTP {response.status_code} (expected {expected_status})")
            print(f"   Response: {response.text[:100]}...")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False, None

def main():
    print("=" * 80)
    print("HR MODULE COMPREHENSIVE VERIFICATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test all HR endpoints
    tests = [
        # Frontend Pages (HTML)
        ("/app/hr", "HR Dashboard Page"),
        ("/app/hr/", "HR Dashboard Page (trailing slash)"),
        ("/app/hr/employees", "Employee List Page"),
        ("/app/hr/employees/", "Employee List Page (trailing slash)"),
        ("/app/hr/employees/new", "New Employee Form"),
        ("/app/hr/employees/new/", "New Employee Form (trailing slash)"),
        ("/app/hr/org-chart", "Organization Chart Page"),
        ("/app/hr/org-chart/", "Organization Chart Page (trailing slash)"),
        
        # API Endpoints - Dashboard (should work - AllowAny permission)
        ("/api/hr/dashboard/summary/", "Dashboard Summary API"),
        ("/api/hr/dashboard/upcoming/?type=birthday&days=30", "Upcoming Birthdays API"),
        ("/api/hr/dashboard/upcoming/?type=anniversary&days=30", "Upcoming Anniversaries API"),
        
        # API Endpoints - Data (requires auth - will return 401)
        ("/api/hr/positions/", "Positions API", 401),
        ("/api/hr/employees/", "Employees API", 401),
        ("/api/hr/org-units/", "Organization Units API", 401),
        ("/api/hr/access-profiles/", "Access Profiles API", 401),
    ]
    
    results = []
    for endpoint, description, *args in tests:
        expected_status = args[0] if args else 200
        success, data = test_endpoint(endpoint, description, expected_status)
        results.append((endpoint, success, description))
        print()
    
    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success Rate: {(successful/total)*100:.1f}%")
    print()
    
    # Group results
    frontend_tests = [r for r in results if r[0].startswith('/app/')]
    api_tests = [r for r in results if r[0].startswith('/api/')]
    
    print("📄 FRONTEND PAGES:")
    for endpoint, success, description in frontend_tests:
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"   {status}: {endpoint} - {description}")
    
    print()
    print("🔌 API ENDPOINTS:")
    for endpoint, success, description in api_tests:
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"   {status}: {endpoint} - {description}")
    
    print()
    print("🎯 KEY FINDINGS:")
    
    frontend_success = sum(1 for _, success, _ in frontend_tests if success)
    api_success = sum(1 for _, success, _ in api_tests if success)
    
    if frontend_success == len(frontend_tests):
        print("✅ All HR frontend pages are accessible")
    else:
        print("⚠️  Some HR frontend pages have issues")
        
    if api_success == len(api_tests):
        print("✅ All HR API endpoints responding correctly")
    else:
        print("⚠️  Some HR API endpoints have issues")
    
    print()
    print("📋 NEXT STEPS:")
    print("1. Access HR pages through browser to test session authentication")
    print("2. Test dropdown functionality in employee form")
    print("3. Verify organization chart loads employee data")
    print("4. Check dashboard displays real-time statistics")
    
    print()
    print("🌐 ACCESS URLS:")
    print(f"   HR Dashboard: {BASE_URL}/app/hr/")
    print(f"   Employee List: {BASE_URL}/app/hr/employees/")
    print(f"   New Employee: {BASE_URL}/app/hr/employees/new/")
    print(f"   Org Chart: {BASE_URL}/app/hr/org-chart/")

if __name__ == "__main__":
    main()
