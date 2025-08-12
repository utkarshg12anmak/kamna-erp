# CV Hub - Developer Quick Reference

## 🚀 Quick Start

### Common Model Operations

```python
from cv_hub.models import CvHubEntry, CvHubGSTRegistration, CvHubAddress, CvHubContact

# Create a customer
customer = CvHubEntry.objects.create(
    legal_name="Customer Corp",
    is_customer=True,
    for_sales=True
)

# Create a supplier with GST
supplier = CvHubEntry.objects.create(
    legal_name="Supplier Inc",
    is_supplier=True,
    for_purchase=True
)

gst = CvHubGSTRegistration.objects.create(
    entry=supplier,
    gstin="27ABCDE1234F1Z5",
    taxpayer_type=CvHubTaxpayerType.REGULAR,
    is_primary=True
)
```

### API Usage

```python
# Using Django REST framework client
from rest_framework.test import APIClient

client = APIClient()
client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

# Get all customers
response = client.get('/api/cv_hub/entries/?is_customer=true')

# Quick search
response = client.get('/api/cv_hub/entries/quick/?q=Corp')

# Get summary
response = client.get('/api/cv_hub/entries/123/summary/')
```

### Template Usage

```html
<!-- Include in your template -->
{% extends 'base_module.html' %}

{% block content %}
<div class="container">
    <h2>Customer Management</h2>
    <!-- Your CV Hub integration here -->
</div>
{% endblock %}
```

## 🔧 Key URLs

| Purpose | URL | Method |
|---------|-----|--------|
| Dashboard | `/app/cv_hub/` | GET |
| List Entries | `/app/cv_hub/entries/` | GET |
| Create Entry | `/app/cv_hub/entries/new/` | GET/POST |
| View Entry | `/app/cv_hub/entries/{id}/` | GET |
| Edit Entry | `/app/cv_hub/entries/{id}/edit/` | GET/POST |
| API Entries | `/api/cv_hub/entries/` | GET/POST/PUT/DELETE |
| API Quick Search | `/api/cv_hub/entries/quick/` | GET |
| API Summary | `/api/cv_hub/entries/{id}/summary/` | GET |

## 🗄️ Model Fields Reference

### CvHubEntry
- `legal_name` - Company legal name (required)
- `display_name` - Display name (optional)
- `constitution` - Business constitution (PROPRIETORSHIP, PARTNERSHIP, etc.)
- `is_customer`, `is_supplier`, `is_vendor`, `is_logistics` - Role flags
- `for_sales`, `for_purchase` - Commerce flags
- `status` - Entry status (ACTIVE, INACTIVE, SUSPENDED)

### CvHubGSTRegistration
- `entry` - Foreign key to CvHubEntry
- `gstin` - 15-character GST number
- `taxpayer_type` - REGULAR, COMPOSITE, UNREGISTERED
- `is_primary` - Primary GST flag (unique per entry)

### CvHubAddress
- `entry` - Foreign key to CvHubEntry
- `type` - BILLING, SHIPPING, BOTH
- `line1`, `line2` - Address lines
- `city`, `state` - Foreign keys to location masters
- `pincode` - Postal code
- `is_default_billing`, `is_default_shipping` - Default flags

### CvHubContact
- `entry` - Foreign key to CvHubEntry
- `full_name` - Contact person name
- `phone` - Phone number (globally unique)
- `email` - Email address
- `designation` - Job title
- `is_primary` - Primary contact flag (unique per entry)

## 🎯 Business Rules

1. **Entry must have at least one role** (customer/supplier/vendor/logistics)
2. **Entry must have at least one commerce flag** (for_sales/for_purchase)
3. **GSTIN must be 15 characters** for registered taxpayers
4. **Only one primary GST** per entry
5. **Only one default billing/shipping address** per entry
6. **Phone numbers are globally unique**
7. **City must belong to selected state**

## 🔍 Common Queries

```python
# Get all active customers
customers = CvHubEntry.objects.filter(
    is_customer=True, 
    status=CvHubEntryStatus.ACTIVE
)

# Get suppliers with GST
suppliers_with_gst = CvHubEntry.objects.filter(
    is_supplier=True,
    gst_registrations__isnull=False
).distinct()

# Get entries by state
mumbai_entries = CvHubEntry.objects.filter(
    addresses__city__name="Mumbai"
).distinct()

# Get primary contacts
primary_contacts = CvHubContact.objects.filter(is_primary=True)
```

## 🔧 Management Commands

```bash
# Seed initial data
python manage.py cv_hub_seed

# Bootstrap permissions
python manage.py cv_hub_bootstrap_roles

# Run smoke tests
python manage.py cv_hub_smoke
```

## 🚨 Troubleshooting

### Common Issues:

1. **GST Validation Error**: Ensure GSTIN is exactly 15 characters for registered taxpayers
2. **City/State Mismatch**: Use the API to get valid city-state combinations
3. **Phone Uniqueness**: Phone numbers must be unique across all contacts
4. **Primary Conflicts**: Only one primary GST/contact per entry allowed

### Debug Commands:

```bash
# Check model counts
python manage.py shell -c "from cv_hub.models import *; print(f'Entries: {CvHubEntry.objects.count()}')"

# Validate data integrity
python manage.py cv_hub_smoke

# Check URL patterns
python manage.py show_urls | grep cv_hub
```

---
*Quick Reference - CV Hub v1.0*
