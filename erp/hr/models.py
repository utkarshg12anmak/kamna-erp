from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator
from simple_history.models import HistoricalRecords

class EmploymentStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    ON_LEAVE = 'ON_LEAVE', 'On Leave'
    INACTIVE = 'INACTIVE', 'Inactive'
    EXITED = 'EXITED', 'Exited'

class SalaryPeriod(models.TextChoices):
    MONTHLY = 'MONTHLY', 'Monthly'
    ANNUAL = 'ANNUAL', 'Annual'

class Gender(models.TextChoices):
    MALE = 'MALE', 'Male'
    FEMALE = 'FEMALE', 'Female'
    OTHER = 'OTHER', 'Other'
    NA = 'NA', 'Prefer not to say'

# Org structure
class OrgUnit(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50, unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    type = models.CharField(max_length=40, default='Department')
    manager = models.ForeignKey('Employee', null=True, blank=True, on_delete=models.SET_NULL, related_name='managed_units')
    status = models.CharField(max_length=12, choices=EmploymentStatus.choices, default=EmploymentStatus.ACTIVE)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name

class Position(models.Model):
    title = models.CharField(max_length=120)
    grade = models.CharField(max_length=40, blank=True)
    family = models.CharField(max_length=60, blank=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.title

pan_validator = RegexValidator(r'^[A-Z]{5}[0-9]{4}[A-Z]$', 'PAN must match AAAAA9999A')
phone_validator = RegexValidator(r'^[0-9+\-\s]{8,20}$', 'Invalid phone number')

class AccessProfile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name

class Employee(models.Model):
    emp_code = models.CharField(max_length=20, unique=True, blank=True)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True)
    gender = models.CharField(max_length=8, choices=Gender.choices, default=Gender.NA)
    email = models.EmailField(blank=True, null=True, unique=True)
    phone = models.CharField(max_length=20, validators=[phone_validator], unique=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='hr/profile/', null=True, blank=True)
    
    # IDs
    aadhaar_last4 = models.CharField(max_length=4, blank=True)
    aadhaar_doc_front = models.FileField(upload_to='hr/docs/aadhaar/', null=True, blank=True)
    aadhaar_doc_back = models.FileField(upload_to='hr/docs/aadhaar/', null=True, blank=True)
    pan_number = models.CharField(max_length=10, validators=[pan_validator], null=True, blank=True)
    pan_doc = models.FileField(upload_to='hr/docs/pan/', null=True, blank=True)
    
    # Job & Org
    department = models.CharField(max_length=120, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    position = models.ForeignKey(Position, null=True, blank=True, on_delete=models.SET_NULL)
    org_unit = models.ForeignKey(OrgUnit, null=True, blank=True, on_delete=models.SET_NULL)
    manager = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    status = models.CharField(max_length=12, choices=EmploymentStatus.choices, default=EmploymentStatus.ACTIVE)
    date_of_joining = models.DateField()
    
    # Payroll
    salary_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    salary_currency = models.CharField(max_length=3, default='INR')
    salary_period = models.CharField(max_length=10, choices=SalaryPeriod.choices, default=SalaryPeriod.MONTHLY)
    
    # Assets (simple flags)
    is_phone_assigned = models.BooleanField(default=False)
    company_assigned_phone_number = models.CharField(max_length=32, blank=True)
    is_laptop_assigned = models.BooleanField(default=False)
    company_assigned_laptop = models.CharField(max_length=64, blank=True)
    
    # Access + auth link
    access_profile = models.ForeignKey(AccessProfile, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='employee_profile')
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='hr_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='hr_updated')
    history = HistoricalRecords()
    
    class Meta:
        indexes = [
            models.Index(models.functions.Lower('first_name'), name='hr_employee_first_name_lower'),
            models.Index(fields=['emp_code'], name='hr_employee_emp_code'),
            models.Index(fields=['status', 'department', 'designation', 'date_of_joining'], name='hr_employee_job_details')
        ]
    
    def __str__(self):
        return f"{self.emp_code or ''} {self.first_name} {self.last_name}".strip()

class EmployeeDocument(models.Model):
    DOC_TYPES = [
        ('AADHAAR', 'Aadhaar'),
        ('PAN', 'PAN'),
        ('OFFER', 'Offer Letter'),
        ('APPOINT', 'Appointment Letter'),
        ('OTHER', 'Other')
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    number = models.CharField(max_length=50, blank=True)
    file = models.FileField(upload_to='hr/docs/other/')
    issued_on = models.DateField(null=True, blank=True)
    valid_till = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

# Field-level audit
class HRFieldChange(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='field_changes')
    field_name = models.CharField(max_length=64)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=16, default='UI')  # UI/API/Import/Script
    request_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        indexes = [models.Index(fields=['employee', 'changed_at'], name='hr_fieldchange_emp_time')]
    
    def __str__(self):
        return f"{self.employee_id}:{self.field_name}"
