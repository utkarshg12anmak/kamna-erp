#!/usr/bin/env python
"""
Final verification script for CV Hub access
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

def test_cv_hub_access():
    print("🔍 CV Hub Access Verification")
    print("=" * 50)
    
    # Get admin user
    admin_user = User.objects.get(username='admin')
    print(f"👤 Testing access for: {admin_user.username}")
    
    # Check groups
    groups = [g.name for g in admin_user.groups.all()]
    print(f"📋 User groups: {groups}")
    print(f"✅ Has 'Customer & Vendor Hub' group: {'Customer & Vendor Hub' in groups}")
    
    # Test web interface access
    print(f"\n🌐 Testing Web Interface:")
    client = Client()
    client.force_login(admin_user)
    
    endpoints = [
        ('/app/cv_hub/', 'Dashboard'),
        ('/app/cv_hub/entries/', 'Entries List'),
    ]
    
    for url, name in endpoints:
        response = client.get(url)
        status = "✅ SUCCESS" if response.status_code == 200 else f"❌ FAILED ({response.status_code})"
        print(f"  {name}: {status}")
    
    # Test API access with JWT
    print(f"\n🔗 Testing API Access:")
    refresh = RefreshToken.for_user(admin_user)
    access_token = str(refresh.access_token)
    
    api_client = Client()
    api_client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
    
    api_endpoints = [
        ('/api/cv_hub/entries/', 'Entries API'),
        ('/api/cv_hub/states/', 'States API'),
        ('/api/auth/me/', 'Auth Me API'),
    ]
    
    for url, name in api_endpoints:
        response = api_client.get(url)
        status = "✅ SUCCESS" if response.status_code == 200 else f"❌ FAILED ({response.status_code})"
        print(f"  {name}: {status}")
        
        # Special check for auth/me endpoint
        if url == '/api/auth/me/' and response.status_code == 200:
            data = response.json()
            has_cv_hub_group = 'Customer & Vendor Hub' in data.get('groups', [])
            print(f"    📋 Returns CV Hub group: {'✅ YES' if has_cv_hub_group else '❌ NO'}")
    
    # Test JavaScript access logic simulation
    print(f"\n📱 Testing JavaScript Access Logic:")
    
    # Simulate the JavaScript checkAccess function
    def simulate_check_access(module_name, user_groups):
        if module_name == 'Admin':
            return 'Admin' in user_groups
        else:
            return module_name in user_groups
    
    module_name = "Customer & Vendor Hub"
    has_access = simulate_check_access(module_name, groups)
    print(f"  Module: '{module_name}'")
    print(f"  Access: {'✅ GRANTED' if has_access else '❌ DENIED'}")
    
    print(f"\n🎉 Final Status:")
    if has_access and all(response.status_code == 200 for response in [client.get('/app/cv_hub/'), client.get('/app/cv_hub/entries/')]):
        print("✅ CV Hub access is WORKING correctly!")
        print("🌟 Admin user can now access all CV Hub features")
    else:
        print("❌ There are still access issues")
    
    print(f"\n📍 Next Steps:")
    print("1. Open browser to http://localhost:8000")
    print("2. Login as admin user")
    print("3. Navigate to CV Hub module")
    print("4. Verify access is granted")

if __name__ == '__main__':
    test_cv_hub_access()
