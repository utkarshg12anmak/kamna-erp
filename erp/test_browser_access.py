#!/usr/bin/env python
"""
Test CV Hub access simulation for browser scenario
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def simulate_browser_access():
    print("🌐 Simulating Browser Access to CV Hub")
    print("=" * 50)
    
    # Create a client (simulates browser)
    client = Client()
    
    # Admin user login (simulates user logged in via web)
    admin = User.objects.get(username='admin')
    client.force_login(admin)
    print(f"✅ Logged in as: {admin.username}")
    
    # Test the main CV Hub page
    print(f"\n📄 Testing CV Hub Pages:")
    
    # Test dashboard
    response = client.get('/app/cv_hub/')
    print(f"  Dashboard (/app/cv_hub/): {response.status_code}")
    
    # Test entries page (where user is having trouble)
    response = client.get('/app/cv_hub/entries/')
    print(f"  Entries (/app/cv_hub/entries/): {response.status_code}")
    
    # Test the auth API with session (simulates JavaScript call)
    print(f"\n🔐 Testing API Auth:")
    
    response = client.get('/api/auth/me/')
    print(f"  Auth API (/api/auth/me/): {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        groups = data.get('groups', [])
        print(f"  User groups: {groups}")
        
        # Simulate JavaScript access check
        module_name = "Customer & Vendor Hub"
        has_access = module_name in groups
        print(f"  Access check for '{module_name}': {'✅ PASS' if has_access else '❌ FAIL'}")
        
        if has_access:
            print(f"\n🎉 SUCCESS: User should have access to CV Hub!")
            print(f"📝 The JavaScript checkAccess() function should return true")
        else:
            print(f"\n❌ ISSUE: User doesn't have the required group")
            print(f"📝 Missing group: '{module_name}'")
    else:
        print(f"  ❌ API Error: {response.status_code}")
    
    # Test CV Hub API endpoints
    print(f"\n🔗 Testing CV Hub API:")
    api_endpoints = [
        '/api/cv_hub/entries/',
        '/api/cv_hub/states/',
    ]
    
    for endpoint in api_endpoints:
        response = client.get(endpoint)
        status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
        print(f"  {endpoint}: {status}")
    
    print(f"\n💡 Troubleshooting Tips:")
    print(f"1. Clear browser cache and cookies")
    print(f"2. Refresh the page (Cmd+R / Ctrl+F5)")
    print(f"3. Check browser console for JavaScript errors")
    print(f"4. Make sure you're logged in to the web interface")

if __name__ == '__main__':
    simulate_browser_access()
