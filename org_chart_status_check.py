#!/usr/bin/env python3
"""
Organization Chart Final Status Check
"""

import subprocess
import json

def test_org_chart():
    print("🔍 Testing Organization Chart API")
    
    try:
        cmd = ["curl", "-s", "http://127.0.0.1:8000/api/hr/dashboard/org-chart/"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            print(f"✅ Success: {len(data)} employees returned")
            print(f"📊 Data type: {type(data).__name__}")
            
            if data:
                sample = data[0]
                print(f"📝 Sample: {sample.get('first_name')} {sample.get('last_name')} - {sample.get('designation')}")
                
            return True, len(data)
        else:
            print(f"❌ Failed: {result.stderr}")
            return False, 0
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, 0

def main():
    print("ORGANIZATION CHART VERIFICATION")
    print("=" * 40)
    
    success, count = test_org_chart()
    
    if success:
        print(f"\n🎉 ORGANIZATION CHART: WORKING")
        print(f"✅ API returns {count} employees")
        print(f"✅ No authentication required")
        print(f"🌐 URL: http://127.0.0.1:8000/app/hr/org-chart/")
    else:
        print(f"\n⚠️ ORGANIZATION CHART: ISSUES")

if __name__ == "__main__":
    main()
