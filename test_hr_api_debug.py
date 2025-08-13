import requests
import json

# Test the employees API endpoint
url = "http://127.0.0.1:8000/api/hr/employees/"

try:
    # Test without authentication first
    response = requests.get(url, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 401:
        print("✓ Expected 401 - Authentication required")
        print(f"Response Body: {response.text}")
    else:
        print(f"Response Body: {response.text[:500]}")
        
except Exception as e:
    print(f"Error: {e}")

# Also test dashboard API (should work without auth)
print("\n" + "="*50)
print("Testing Dashboard API (should work):")

try:
    dashboard_url = "http://127.0.0.1:8000/api/hr/dashboard/summary/"
    response = requests.get(dashboard_url, timeout=5)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Dashboard Data: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
