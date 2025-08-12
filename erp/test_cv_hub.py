#!/usr/bin/env python
"""
Quick CV Hub functionality test
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from cv_hub.models import CvHubEntry, CvHubState, CvHubCity
from cv_hub.api.serializers import CvHubEntrySerializer
from django.test import Client
from django.urls import reverse

def test_models():
    print("=== Testing Models ===")
    
    # Test data availability
    entries = CvHubEntry.objects.all()
    states = CvHubState.objects.all()
    cities = CvHubCity.objects.all()
    
    print(f"✓ Entries: {entries.count()}")
    print(f"✓ States: {states.count()}")  
    print(f"✓ Cities: {cities.count()}")
    
    if entries.exists():
        entry = entries.first()
        print(f"✓ Sample entry: {entry.legal_name}")
        print(f"  - Roles: Customer={entry.is_customer}, Supplier={entry.is_supplier}")
        print(f"  - Commerce: Sales={entry.for_sales}, Purchase={entry.for_purchase}")

def test_serializers():
    print("\n=== Testing Serializers ===")
    
    entries = CvHubEntry.objects.all()
    if entries.exists():
        entry = entries.first()
        serializer = CvHubEntrySerializer(entry)
        data = serializer.data
        
        print(f"✓ Serialized entry ID: {data['id']}")
        print(f"✓ Legal name: {data['legal_name']}")
        print(f"✓ Commerce label: {data['commerce_label']}")
        print(f"✓ Role label: {data['role_label']}")

def test_views():
    print("\n=== Testing Views ===")
    
    client = Client()
    
    # Test CV Hub dashboard
    try:
        response = client.get(reverse('module_cv_hub'))
        print(f"✓ Dashboard: {response.status_code}")
    except Exception as e:
        print(f"✗ Dashboard error: {e}")
    
    # Test entries list
    try:
        response = client.get(reverse('cv_hub_entries'))
        print(f"✓ Entries list: {response.status_code}")
    except Exception as e:
        print(f"✗ Entries list error: {e}")

def test_api():
    print("\n=== Testing API ===")
    
    client = Client()
    
    # Test API endpoints
    endpoints = [
        '/api/cv_hub/entries/',
        '/api/cv_hub/entries/quick/',
        '/api/cv_hub/states/',
        '/api/cv_hub/cities/',
    ]
    
    for endpoint in endpoints:
        try:
            response = client.get(endpoint)
            print(f"✓ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint} error: {e}")

if __name__ == '__main__':
    print("CV Hub Functionality Test")
    print("=" * 50)
    
    test_models()
    test_serializers()
    test_views()
    test_api()
    
    print("\n" + "=" * 50)
    print("✅ CV Hub test completed!")
