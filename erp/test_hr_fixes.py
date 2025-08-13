#!/usr/bin/env python
"""
Test script to verify HR module fixes
"""
import os
import sys
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_hr_fixes():
    """Test both HR module fixes"""
    print("🧪 Testing HR Module Fixes...")
    
    # Create test client
    client = Client()
    
    # Test 1: Org Chart Page Access
    print("\n1️⃣ Testing Org Chart Page Access...")
    try:
        response = client.get('/app/hr/org-chart')
        if response.status_code == 200:
            print("✅ Org chart page loads successfully")
            print(f"   Status Code: {response.status_code}")
        else:
            print(f"❌ Org chart page failed: Status {response.status_code}")
            if hasattr(response, 'content'):
                print(f"   Error: {response.content.decode()[:200]}...")
    except Exception as e:
        print(f"❌ Org chart page error: {e}")
    
    # Test 2: Employee Form Page Access
    print("\n2️⃣ Testing Employee Form Page Access...")
    try:
        response = client.get('/app/hr/employees/new')
        if response.status_code == 200:
            print("✅ Employee form page loads successfully")
            print(f"   Status Code: {response.status_code}")
            
            # Check if form has submit button
            content = response.content.decode()
            if 'Save Employee' in content:
                print("✅ Save Employee button found in form")
            else:
                print("⚠️ Save Employee button not found in form")
                
            if 'Save as Draft' in content:
                print("✅ Save as Draft button found in form")
            else:
                print("⚠️ Save as Draft button not found in form")
                
        else:
            print(f"❌ Employee form page failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Employee form page error: {e}")
    
    # Test 3: Template Structure
    print("\n3️⃣ Testing Template Structure...")
    try:
        # Check if templates exist
        templates_to_check = [
            'templates/hr/org_chart_content.html',
            'templates/hr/employee_form.html'
        ]
        
        for template in templates_to_check:
            if os.path.exists(template):
                print(f"✅ Template exists: {template}")
            else:
                print(f"❌ Template missing: {template}")
                
    except Exception as e:
        print(f"❌ Template check error: {e}")
    
    print("\n🎯 HR Module Fixes Test Complete!")

if __name__ == '__main__':
    test_hr_fixes()
