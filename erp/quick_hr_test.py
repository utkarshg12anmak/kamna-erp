#!/usr/bin/env python
"""
Quick HR Fix Verification
"""
from django.test import TestCase, Client

class HRFixTest(TestCase):
    def test_org_chart_access(self):
        """Test org chart page access"""
        client = Client()
        response = client.get('/app/hr/org-chart')
        print(f"Org Chart Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.content.decode()[:500]}")
        
    def test_employee_form_access(self):
        """Test employee form access"""
        client = Client()
        response = client.get('/app/hr/employees/new')
        print(f"Employee Form Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.content.decode()[:500]}")

if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
    django.setup()
    
    # Quick test
    test = HRFixTest()
    test.test_org_chart_access()
    test.test_employee_form_access()
