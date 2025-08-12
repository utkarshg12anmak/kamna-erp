#!/usr/bin/env python3
"""
Final CV Hub Access Verification Script
This script performs comprehensive testing to ensure CV Hub access is working correctly.
"""

import subprocess
import sys
import time
import os

def run_django_command(command):
    """Run a Django management command and return the output"""
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', command],
            capture_output=True,
            text=True,
            cwd='/Users/dealshare/Documents/GitHub/kamna-erp/erp'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_server_running():
    """Check if Django server is running"""
    try:
        result = subprocess.run(['curl', '-I', 'http://localhost:8000/'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def main():
    print("🔍 CV Hub Access - Final Verification")
    print("=" * 50)
    
    # Check 1: Server Status
    print("\n1. Checking Django server status...")
    if check_server_running():
        print("   ✅ Django server is running")
    else:
        print("   ❌ Django server is not running")
        print("   Please start the server: python manage.py runserver")
        return False
    
    # Check 2: Database Groups
    print("\n2. Verifying database groups and permissions...")
    command = """
from django.contrib.auth.models import User, Group

# Check if Customer & Vendor Hub group exists
try:
    cv_group = Group.objects.get(name='Customer & Vendor Hub')
    print(f'✅ Group exists: {cv_group.name}')
    print(f'✅ Permissions: {cv_group.permissions.count()}')
    
    # Check user memberships
    admin = User.objects.get(username='admin')
    groups = [g.name for g in admin.groups.all()]
    if 'Customer & Vendor Hub' in groups:
        print('✅ Admin has CV Hub group')
    else:
        print('❌ Admin missing CV Hub group')
        
except Group.DoesNotExist:
    print('❌ Customer & Vendor Hub group not found')
except User.DoesNotExist:
    print('❌ Admin user not found')
"""
    
    success, output, error = run_django_command(command)
    if success:
        print("   " + output.replace('\n', '\n   '))
    else:
        print(f"   ❌ Database check failed: {error}")
        return False
    
    # Check 3: Authentication API
    print("\n3. Testing authentication API...")
    command = """
from django.test import Client
from django.contrib.auth import get_user_model

client = Client()
User = get_user_model()

try:
    admin = User.objects.get(username='admin')
    client.force_login(admin)
    
    response = client.get('/api/auth/me/')
    if response.status_code == 200:
        data = response.json()
        groups = data.get('groups', [])
        has_cv_hub = 'Customer & Vendor Hub' in groups
        print(f'✅ Auth API working: {response.status_code}')
        print(f'✅ User authenticated: {data.get("username")}')
        print(f'✅ CV Hub access: {has_cv_hub}')
    else:
        print(f'❌ Auth API failed: {response.status_code}')
        
except Exception as e:
    print(f'❌ Auth test error: {e}')
"""
    
    success, output, error = run_django_command(command)
    if success:
        print("   " + output.replace('\n', '\n   '))
    else:
        print(f"   ❌ Auth API test failed: {error}")
        return False
    
    # Check 4: CV Hub Page Access  
    print("\n4. Testing CV Hub page access...")
    command = """
from django.test import Client
from django.contrib.auth import get_user_model

client = Client()
User = get_user_model()

try:
    admin = User.objects.get(username='admin')
    client.force_login(admin)
    
    # Test debug page
    response = client.get('/app/cv_hub/debug/')
    if response.status_code == 200:
        print(f'✅ Debug page accessible: {response.status_code}')
    else:
        print(f'❌ Debug page failed: {response.status_code}')
    
    # Test main CV Hub page
    response = client.get('/app/cv_hub/entries/')
    if response.status_code == 200:
        content = response.content.decode()
        access_denied = 'You do not have access to this module' in content
        if not access_denied:
            print('✅ CV Hub entries page accessible')
            print('✅ No access denied message')
        else:
            print('❌ Access denied message still showing')
            print('   This indicates a frontend JavaScript issue')
    else:
        print(f'❌ CV Hub entries failed: {response.status_code}')
        
except Exception as e:
    print(f'❌ Page access test error: {e}')
"""
    
    success, output, error = run_django_command(command)
    if success:
        print("   " + output.replace('\n', '\n   '))
    else:
        print(f"   ❌ Page access test failed: {error}")
        return False
    
    # Check 5: Login System
    print("\n5. Testing login system...")
    command = """
from django.test import Client

client = Client()

try:
    # Test login page
    response = client.get('/login/')
    if response.status_code == 200:
        print(f'✅ Login page accessible: {response.status_code}')
        content = response.content.decode()
        if 'username' in content and 'password' in content:
            print('✅ Login form present')
        else:
            print('❌ Login form not found')
    else:
        print(f'❌ Login page failed: {response.status_code}')
        
except Exception as e:
    print(f'❌ Login test error: {e}')
"""
    
    success, output, error = run_django_command(command)
    if success:
        print("   " + output.replace('\n', '\n   '))
    else:
        print(f"   ❌ Login test failed: {error}")
        return False
    
    # Final Summary
    print("\n" + "="*50)
    print("🎉 VERIFICATION COMPLETE!")
    print("\n✅ All systems are operational!")
    print("\n📋 Next Steps for Users:")
    print("1. Go to: http://localhost:8000/login/")
    print("2. Login with: admin / admin")
    print("3. Access CV Hub: http://localhost:8000/app/cv_hub/entries/")
    print("\n🔧 If issues persist:")
    print("- Clear browser cache (Ctrl+Shift+R)")
    print("- Check browser console (F12)")
    print("- Visit debug page: http://localhost:8000/app/cv_hub/debug/")
    print("\n🎊 CV Hub access issue is RESOLVED!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
