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
    email = models.EmailField(blank=True, null=True, unique=True)
    phone = models.CharField(max_length=20, validators=[phone_validator], unique=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='hr/profile/', null=True, blank=True)
    aadhaar_last4 = models.CharField(max_length=4, blank=True)
    aadhaar_doc_front = models.FileField(upload_to='hr/docs/aadhaar/', null=True, blank=True)
    aadhaar_doc_back = models.FileField(upload_to='hr/docs/aadhaar/', null=True, blank=True)
    pan_number = models.CharField(max_length=10, validators=[pan_validator], null=True, blank=True)
    pan_doc = models.FileField(upload_to='hr/docs/pan/', null=True, blank=True)
    department = models.CharField(max_length=120, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    manager = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='team')
    status = models.CharField(max_length=12, choices=EmploymentStatus.choices, default=EmploymentStatus.ACTIVE)
    date_of_joining = models.DateField()
    salary_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    salary_currency = models.CharField(max_length=3, default='INR')
    salary_period = models.CharField(max_length=10, choices=SalaryPeriod.choices, default=SalaryPeriod.MONTHLY)
    access_profile = models.ForeignKey(AccessProfile, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='employee_profile')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='hr_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='hr_updated')
    history = HistoricalRecords()
    class Meta:
        indexes = [
            models.Index(models.functions.Lower('first_name')),
            models.Index(fields=['emp_code']),
            models.Index(fields=['status','department','designation','date_of_joining'])
        ]
    def __str__(self):
        return f"{self.emp_code or ''} {self.first_name} {self.last_name}".strip()

class EmployeeDocument(models.Model):
    DOC_TYPES = [
        ('AADHAAR','Aadhaar'),
        ('PAN','PAN'),
        ('OFFER','Offer Letter'),
        ('APPOINT','Appointment Letter'),
        ('OTHER','Other')
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
    def __str__(self):
        return f"{self.employee_id} {self.doc_type}"
