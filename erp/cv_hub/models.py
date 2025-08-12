from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from simple_history.models import HistoricalRecords

# ---- Masters ----
class CvHubState(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    def __str__(self): return self.name

class CvHubCity(models.Model):
    state = models.ForeignKey(CvHubState, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=120)
    class Meta:
        unique_together = [('state','name')]
    def __str__(self): return f"{self.name}, {self.state.code}"

# ---- Core entry (formerly 'partner') ----
class CvHubEntryStatus(models.TextChoices):
    ACTIVE='ACTIVE','Active'
    INACTIVE='INACTIVE','Inactive'
    BLACKLISTED='BLACKLISTED','Blacklisted'

class CvHubConstitution(models.TextChoices):
    INDIVIDUAL='INDIVIDUAL','Individual'
    PROPRIETORSHIP='PROPRIETORSHIP','Proprietorship'
    PARTNERSHIP='PARTNERSHIP','Partnership'
    PVTLTD='PVTLTD','Private Limited'
    LLP='LLP','LLP'
    TRUST='TRUST','Trust'
    GOVT='GOVT','Government'
    OTHER='OTHER','Other'

class CvHubEntry(models.Model):
    legal_name = models.CharField(max_length=200)
    trade_name = models.CharField(max_length=200, blank=True)
    constitution = models.CharField(max_length=20, choices=CvHubConstitution.choices, default=CvHubConstitution.OTHER)
    status = models.CharField(max_length=12, choices=CvHubEntryStatus.choices, default=CvHubEntryStatus.ACTIVE)
    # roles
    is_customer = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)
    is_vendor   = models.BooleanField(default=False)
    is_logistics= models.BooleanField(default=False)
    # commercial usage flags
    for_sales    = models.BooleanField(default=False)
    for_purchase = models.BooleanField(default=False)
    website = models.URLField(blank=True)
    tags = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='cv_hub_entry_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='cv_hub_entry_updated')
    history = HistoricalRecords()
    class Meta:
        indexes = [models.Index(fields=['status','constitution']), models.Index(fields=['for_sales','for_purchase'])]
    def __str__(self): return self.legal_name

# ---- GST Registration ----
class CvHubTaxpayerType(models.TextChoices):
    REGULAR='REGULAR','Regular'
    COMPOSITION='COMPOSITION','Composition'
    CASUAL='CASUAL','Casual'
    UNREGISTERED='UNREGISTERED','Unregistered'
    OTHER='OTHER','Other'

class CvHubGSTStatus(models.TextChoices):
    ACTIVE='ACTIVE','Active'
    CANCELLED='CANCELLED','Cancelled'
    SUSPENDED='SUSPENDED','Suspended'

class CvHubGSTRegistration(models.Model):
    entry = models.ForeignKey(CvHubEntry, on_delete=models.CASCADE, related_name='registrations')
    taxpayer_type = models.CharField(max_length=20, choices=CvHubTaxpayerType.choices, default=CvHubTaxpayerType.UNREGISTERED)
    gstin = models.CharField(max_length=15, null=True, blank=True, unique=True)  # Made unique
    # Business details
    legal_name_of_business = models.CharField(max_length=200)
    trade_name = models.CharField(max_length=200, blank=True)
    effective_date_of_registration = models.DateField(null=True, blank=True)
    constitution_of_business = models.CharField(max_length=20, choices=CvHubConstitution.choices, default=CvHubConstitution.OTHER)
    gstin_status = models.CharField(max_length=20, choices=CvHubGSTStatus.choices, default=CvHubGSTStatus.ACTIVE)
    principal_place_of_business = models.TextField(blank=True)
    business_activities = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=CvHubGSTStatus.choices, default=CvHubGSTStatus.ACTIVE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='cv_hub_gst_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='cv_hub_gst_updated')
    history = HistoricalRecords()
    class Meta:
        indexes = [models.Index(fields=['gstin']), models.Index(fields=['taxpayer_type','gstin_status'])]
        constraints = [
            models.UniqueConstraint(
                fields=['gstin'], 
                condition=models.Q(gstin__isnull=False) & ~models.Q(gstin=''),
                name='unique_gstin_when_not_null'
            )
        ]
    def __str__(self): return self.gstin or f"UNREG:{self.entry_id}"

# ---- Addresses ----
class CvHubAddressType(models.TextChoices):
    REGISTERED='REGISTERED','Registered Office'
    BILLING='BILLING','Billing'
    SHIPPING='SHIPPING','Shipping'
    PLANT='PLANT','Plant/Factory'
    OTHER='OTHER','Other'

class CvHubAddress(models.Model):
    entry = models.ForeignKey(CvHubEntry, on_delete=models.CASCADE, related_name='addresses')
    type = models.CharField(max_length=20, choices=CvHubAddressType.choices, default=CvHubAddressType.OTHER)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    pincode = models.CharField(max_length=10)
    state = models.ForeignKey(CvHubState, on_delete=models.PROTECT)
    city  = models.ForeignKey(CvHubCity, on_delete=models.PROTECT)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude= models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default_billing = models.BooleanField(default=False)
    is_default_shipping= models.BooleanField(default=False)
    history = HistoricalRecords()
    class Meta:
        indexes = [models.Index(fields=['state','city'])]

# ---- Contacts ----
_phone_norm = RegexValidator(r'^[0-9+\-\s]{8,10}$','Phone number must be 8-10 digits')

class CvHubDesignation(models.TextChoices):
    CEO = 'CEO', 'Chief Executive Officer'
    CFO = 'CFO', 'Chief Financial Officer'
    CTO = 'CTO', 'Chief Technology Officer'
    MANAGER = 'MANAGER', 'Manager'
    ASSISTANT_MANAGER = 'ASSISTANT_MANAGER', 'Assistant Manager'
    EXECUTIVE = 'EXECUTIVE', 'Executive'
    SENIOR_EXECUTIVE = 'SENIOR_EXECUTIVE', 'Senior Executive'
    ACCOUNTANT = 'ACCOUNTANT', 'Accountant'
    SALES_MANAGER = 'SALES_MANAGER', 'Sales Manager'
    PURCHASE_MANAGER = 'PURCHASE_MANAGER', 'Purchase Manager'
    DIRECTOR = 'DIRECTOR', 'Director'
    PARTNER = 'PARTNER', 'Partner'
    PROPRIETOR = 'PROPRIETOR', 'Proprietor'
    OTHER = 'OTHER', 'Other'

class CvHubContact(models.Model):
    entry = models.ForeignKey(CvHubEntry, on_delete=models.CASCADE, related_name='contacts')
    full_name = models.CharField(max_length=150)  # Keep temporarily for migration
    first_name = models.CharField(max_length=75, blank=True)
    last_name = models.CharField(max_length=75, blank=True)
    designation = models.CharField(max_length=20, choices=CvHubDesignation.choices, default=CvHubDesignation.OTHER, blank=True)
    phone = models.CharField(max_length=15, validators=[_phone_norm])  # Removed unique constraint
    email = models.EmailField(blank=True)
    is_primary = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='cv_hub_contact_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='cv_hub_contact_updated')
    history = HistoricalRecords()
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['entry', 'phone'], name='unique_phone_per_entry')
        ]
    
    def save(self, *args, **kwargs):
        # Auto-populate first_name and last_name from full_name if not set
        if self.full_name and not self.first_name and not self.last_name:
            name_parts = self.full_name.strip().split()
            self.first_name = name_parts[0] if name_parts else ''
            self.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        # Auto-populate full_name from first_name and last_name if not set
        elif self.first_name and not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)
    
    def __str__(self): return f"{self.full_name} ({self.entry_id})"
