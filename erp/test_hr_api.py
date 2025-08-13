#!/usr/bin/env python3
"""
HR API Test Script
Tests if the HR API endpoints are working correctly
"""

import requests
import json
from datetime import date

def test_hr_api():
    base_url = "http://localhost:8000/api/hr"
    
    print("🔍 TESTING HR API ENDPOINTS")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        "/employees/",
        "/org-units/",
        "/positions/", 
        "/access-profiles/",
        "/employee-documents/"
    ]
    
    for endpoint in endpoints:
        url = base_url + endpoint
        try:
            print(f"Testing: {url}")
            response = requests.get(url, timeout=5)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'results' in data:
                    print(f"  Results: {len(data['results'])} items")
                elif isinstance(data, list):
                    print(f"  Results: {len(data)} items")
                else:
                    print(f"  Response: {type(data)}")
            elif response.status_code == 403:
                print("  ⚠️  Authentication required")
            else:
                print(f"  ❌ Error: {response.text[:100]}")
            
        except requests.exceptions.ConnectionError:
            print(f"  ❌ Connection refused - server not running")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    # Test creating an employee via API
    print("🧪 TESTING EMPLOYEE CREATION")
    print("-" * 30)
    
    employee_data = {
        "first_name": "Test",
        "last_name": "Employee",
        "phone": "+91 9876543210",
        "email": "test@example.com",
        "date_of_joining": str(date.today()),
        "department": "IT",
        "designation": "Software Engineer"
    }
    
    try:
        url = base_url + "/employees/"
        print(f"POST {url}")
        print(f"Data: {json.dumps(employee_data, indent=2)}")
        
        response = requests.post(url, json=employee_data, timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Employee created successfully!")
            print(f"ID: {result.get('id')}")
            print(f"Employee Code: {result.get('emp_code')}")
        elif response.status_code == 403:
            print("⚠️  Authentication required for creation")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_hr_api()
