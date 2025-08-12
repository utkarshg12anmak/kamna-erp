#!/usr/bin/env python
"""
Comprehensive test to verify the GST duplicate error message solution.
This test validates that users now see meaningful error messages like:
"GSTIN 12ABCDE3456F1Z5 is already registered to ABC Company Ltd"
instead of "Unknown error"
"""
import os
import sys
import django

# Add the erp directory to the path
sys.path.insert(0, '/Users/dealshare/Documents/GitHub/kamna-erp/erp')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from rest_framework.test import APIClient
from cv_hub.models import CvHubEntry, CvHubGSTRegistration
import json

def test_meaningful_gst_error_messages():
    """
    Test that demonstrates the solution to the original issue:
    When trying to create a duplicate GST entry, users now see:
    "GSTIN 12ABCDE3456F1Z5 is already registered to ABC Company Ltd"
    instead of "Unknown error"
    """
    
    print("🧪 TESTING GST DUPLICATE ERROR MESSAGE SOLUTION")
    print("=" * 60)
    
    # Clean up any existing test data
    CvHubGSTRegistration.objects.filter(gstin__startswith='DEMO').delete()
    CvHubEntry.objects.filter(legal_name__startswith='Demo').delete()
    
    # Create realistic vendor entries
    vendor_abc = CvHubEntry.objects.create(
        legal_name="Demo ABC Manufacturing Ltd",
        trade_name="ABC Mfg",
        is_vendor=True,
        for_purchase=True
    )
    
    vendor_xyz = CvHubEntry.objects.create(
        legal_name="Demo XYZ Supplies Pvt Ltd", 
        trade_name="XYZ Supplies",
        is_vendor=True,
        for_purchase=True
    )
    
    # Create first GST registration for ABC Manufacturing
    gst_abc = CvHubGSTRegistration.objects.create(
        entry=vendor_abc,
        taxpayer_type='REGULAR',
        gstin='DEMO12345678901',
        legal_name_of_business='Demo ABC Manufacturing Ltd',
        is_primary=True
    )
    
    print(f"✅ Created GST registration:")
    print(f"   GSTIN: {gst_abc.gstin}")
    print(f"   Vendor: {vendor_abc.legal_name}")
    print()
    
    # Now try to create duplicate GST via API (this is what happens when user submits form)
    client = APIClient()
    duplicate_request = {
        'entry': vendor_xyz.id,
        'taxpayer_type': 'REGULAR', 
        'gstin': 'DEMO12345678901',  # Same GSTIN as ABC Manufacturing
        'legal_name_of_business': 'Demo XYZ Supplies Pvt Ltd',
        'is_primary': True
    }
    
    print("🔄 Attempting to create duplicate GST registration...")
    print(f"   Trying to assign GSTIN {duplicate_request['gstin']} to {vendor_xyz.legal_name}")
    print()
    
    # This simulates the AJAX request from the frontend
    response = client.post('/api/cv_hub/registrations/', duplicate_request, format='json')
    
    print("📤 API Response:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Data: {response.data}")
    print()
    
    # This is exactly what our frontend JavaScript now does
    if response.status_code == 400:
        errorData = response.data
        errorMessage = 'Error saving GST registration: '
        
        # Frontend error parsing logic (implemented in both cv_hub_form.html and cv_hub_view.html)
        if errorData.get('gstin') and len(errorData['gstin']) > 0:
            errorMessage += errorData['gstin'][0]
        elif errorData.get('non_field_errors') and len(errorData['non_field_errors']) > 0:
            errorMessage += errorData['non_field_errors'][0]
        elif errorData.get('detail'):
            errorMessage += errorData['detail']
        else:
            # Try to extract any meaningful error message from the response
            firstError = None
            for value in errorData.values():
                if isinstance(value, list) and len(value) > 0:
                    firstError = value
                    break
            if firstError:
                errorMessage += firstError[0]
            else:
                errorMessage += 'Unknown error'
        
        print("🖥️  FRONTEND ERROR MESSAGE (what user sees):")
        print(f"   '{errorMessage}'")
        print()
        
        # Validate the solution
        if 'already registered to' in errorMessage and vendor_abc.legal_name in errorMessage:
            print("🎯 ✅ SUCCESS! The error message now contains:")
            print(f"   ✓ The GSTIN number: {gst_abc.gstin}")
            print(f"   ✓ The existing vendor name: {vendor_abc.legal_name}")
            print(f"   ✓ Clear indication that GST already exists")
            print()
            print("🔧 SOLUTION SUMMARY:")
            print("   • Modified serializer validation to provide meaningful error messages")
            print("   • Updated frontend error handling in cv_hub_form.html and cv_hub_view.html")
            print("   • Removed database constraints to allow custom validation")
            print("   • Users now see exactly which vendor already has the GST number")
            print()
            print("🚀 ORIGINAL ISSUE RESOLVED!")
            print("   Before: 'Error saving GST registration: Unknown error'")
            print(f"   After:  '{errorMessage}'")
            
        else:
            print("❌ FAILED: Error message still doesn't contain vendor information")
            print(f"   Expected to contain: 'already registered to {vendor_abc.legal_name}'")
            print(f"   Actual message: '{errorMessage}'")
    
    else:
        print(f"❌ UNEXPECTED: Expected status 400 but got {response.status_code}")
    
    # Clean up test data
    gst_abc.delete()
    vendor_abc.delete()
    vendor_xyz.delete()
    
    print()
    print("🧹 Test cleanup completed")
    print("=" * 60)

def test_edge_cases():
    """Test edge cases to ensure robustness"""
    
    print("🧪 TESTING EDGE CASES")
    print("=" * 30)
    
    # Test case-insensitive GSTIN handling
    entry1 = CvHubEntry.objects.create(legal_name="Test Case Company 1", is_vendor=True, for_purchase=True)
    entry2 = CvHubEntry.objects.create(legal_name="Test Case Company 2", is_vendor=True, for_purchase=True)
    
    # Create GST with lowercase
    gst1 = CvHubGSTRegistration.objects.create(
        entry=entry1, taxpayer_type='REGULAR', 
        gstin='test12345678902', legal_name_of_business='Test Case Company 1'
    )
    
    # Try to create duplicate with uppercase (should be caught)
    client = APIClient()
    response = client.post('/api/cv_hub/registrations/', {
        'entry': entry2.id, 'taxpayer_type': 'REGULAR',
        'gstin': 'TEST12345678902', 'legal_name_of_business': 'Test Case Company 2'
    }, format='json')
    
    if response.status_code == 400 and 'already registered to' in str(response.data):
        print("✅ Case-insensitive GSTIN validation works")
    else:
        print("❌ Case-insensitive GSTIN validation failed")
    
    # Clean up
    gst1.delete()
    entry1.delete()
    entry2.delete()
    
    print("🧹 Edge case tests completed")
    print()

if __name__ == "__main__":
    test_meaningful_gst_error_messages()
    test_edge_cases()
    print("🎉 ALL TESTS COMPLETED!")
