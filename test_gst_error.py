#!/usr/bin/env python
"""
Test script to verify GST registration error handling is working correctly.
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

def test_gst_duplicate_error():
    """Test that duplicate GST registration returns proper error message"""
    
    # Clean up existing test data
    CvHubGSTRegistration.objects.filter(gstin__startswith='TEST').delete()
    CvHubEntry.objects.filter(legal_name__startswith='Test Error').delete()
    
    # Create a test entry
    entry = CvHubEntry.objects.create(
        legal_name="Test Error Company",
        is_customer=True,
        for_sales=True
    )
    
    # Create first GST registration
    gst1 = CvHubGSTRegistration.objects.create(
        entry=entry,
        taxpayer_type='REGULAR',
        gstin='TEST123456789AB',
        legal_name_of_business='Test Error Company Ltd',
        is_primary=True
    )
    print(f"✅ Created first GST registration: {gst1.gstin}")
    
    # Create another entry to test duplicate GST
    entry2 = CvHubEntry.objects.create(
        legal_name="Test Error Company 2",
        is_customer=True,
        for_sales=True
    )
    
    # Test API call with duplicate GSTIN
    client = APIClient()
    duplicate_data = {
        'entry': entry2.id,
        'taxpayer_type': 'REGULAR',
        'gstin': 'TEST123456789AB',  # Same GSTIN as first registration
        'legal_name_of_business': 'Test Error Company 2 Ltd',
        'is_primary': False
    }
    
    response = client.post('/api/cv_hub/registrations/', duplicate_data, format='json')
    
    print(f"❌ Duplicate GST API Response:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Data: {response.data}")
    
    # Test the frontend error parsing logic
    if response.status_code == 400:
        errorData = response.data
        errorMessage = 'Error saving GST registration: '
        
        # This is the logic we implemented in the frontend
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
        
        print(f"📱 Frontend Error Message: {errorMessage}")
        
        # Check if the error message contains vendor information
        if 'already registered to' in errorMessage.lower():
            print("✅ SUCCESS: Error message contains vendor information!")
        else:
            print("❌ WARNING: Error message does not contain vendor information")
    
    # Clean up
    gst1.delete()
    entry.delete()
    entry2.delete()
    print("🧹 Cleaned up test data")

if __name__ == "__main__":
    print("🧪 Testing GST Registration Error Handling...")
    print("="*50)
    test_gst_duplicate_error()
    print("="*50)
    print("✅ Test completed!")
