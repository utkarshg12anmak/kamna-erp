#!/usr/bin/env python3
"""
CV Hub Final Demo Script
Demonstrates all implemented functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from cv_hub.models import *
from django.db import transaction

def demo_cv_hub():
    print("🏢 CV Hub Final Demonstration")
    print("=" * 50)
    
    # 1. Show existing data
    print("\n1. 📊 Current Database State:")
    print(f"   States: {CvHubState.objects.count()}")
    print(f"   Cities: {CvHubCity.objects.count()}")
    print(f"   Entries: {CvHubEntry.objects.count()}")
    print(f"   GST Registrations: {CvHubGSTRegistration.objects.count()}")
    print(f"   Addresses: {CvHubAddress.objects.count()}")
    print(f"   Contacts: {CvHubContact.objects.count()}")
    
    # 2. Show sample entries
    print("\n2. 📋 Sample Entries:")
    for entry in CvHubEntry.objects.all()[:3]:
        roles = []
        if entry.is_customer: roles.append("Customer")
        if entry.is_supplier: roles.append("Supplier")
        if entry.is_vendor: roles.append("Vendor")
        if entry.is_logistics: roles.append("Logistics")
        
        usage = []
        if entry.for_sales: usage.append("Sales")
        if entry.for_purchase: usage.append("Purchase")
        
        primary_gstin = entry.registrations.filter(is_primary=True).first()
        gstin = primary_gstin.gstin if primary_gstin else "Unregistered"
        
        print(f"   • {entry.legal_name}")
        print(f"     Roles: {', '.join(roles)}")
        print(f"     Usage: {', '.join(usage)}")
        print(f"     GSTIN: {gstin}")
        print(f"     Status: {entry.status}")
    
    # 3. Show API endpoints
    print("\n3. 🔗 Available API Endpoints:")
    endpoints = [
        ("GET /api/cv_hub/entries/", "List all customer/vendor entries"),
        ("POST /api/cv_hub/entries/", "Create new entry"),
        ("GET /api/cv_hub/entries/{id}/", "Get entry details"),
        ("GET /api/cv_hub/entries/quick/", "Quick search for typeahead"),
        ("GET /api/cv_hub/entries/{id}/summary/", "Entry summary"),
        ("GET /api/cv_hub/states/", "List all states"),
        ("GET /api/cv_hub/cities/?state={id}", "List cities by state"),
        ("CRUD /api/cv_hub/registrations/", "GST registrations"),
        ("CRUD /api/cv_hub/addresses/", "Entry addresses"),
        ("CRUD /api/cv_hub/contacts/", "Entry contacts"),
    ]
    
    for endpoint, description in endpoints:
        print(f"   • {endpoint:<35} - {description}")
    
    # 4. Show frontend URLs
    print("\n4. 🖥️  Frontend URLs:")
    urls = [
        ("/app/cv_hub/", "CV Hub dashboard"),
        ("/app/cv_hub/entries/", "Entries list with filters"),
        ("/app/cv_hub/entries/new/", "Quick create form"),
        ("/app/cv_hub/entries/{id}/", "Entry detail view"),
        ("/app/cv_hub/entries/{id}/edit/", "Entry edit form"),
    ]
    
    for url, description in urls:
        print(f"   • {url:<30} - {description}")
    
    # 5. Show key features
    print("\n5. ⚡ Key Features Implemented:")
    features = [
        "✅ No permission restrictions - accessible to all users",
        "✅ Advanced filtering by roles, usage, status, geography",
        "✅ State→City cascade dropdowns",
        "✅ GST validation (15-character GSTIN)",
        "✅ Primary contact/address/registration logic",
        "✅ Full-text search across all fields",
        "✅ Quick create modal",
        "✅ Comprehensive form validation",
        "✅ Historical tracking with simple_history",
        "✅ Commerce label generation (Sales/Purchase/Both)",
        "✅ Phone number normalization and uniqueness",
        "✅ Module hub integration",
        "✅ Bootstrap 5 responsive UI",
        "✅ API filtering, searching, ordering",
        "✅ Database seeding with Indian states/cities",
    ]
    
    for feature in features:
        print(f"   {feature}")
    
    # 6. Show sample API call
    print("\n6. 📡 Sample API Usage:")
    print("   curl 'http://localhost:8000/api/cv_hub/entries/?for_sales=true&status=ACTIVE'")
    print("   curl 'http://localhost:8000/api/cv_hub/cities/?state=1'")
    print("   curl 'http://localhost:8000/api/cv_hub/entries/quick/?q=ABC'")
    
    print("\n🎉 CV Hub Implementation Complete!")
    print("   Access the application at: http://localhost:8000/app/cv_hub/entries/")
    print("   Module Hub: http://localhost:8000/app/")

if __name__ == "__main__":
    demo_cv_hub()
