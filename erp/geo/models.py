from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

class State(models.Model):
    """
    State master data model.
    
    Audit fields (created_at, updated_at, created_by, updated_by) are automatically
    managed by the system and should not be manually edited.
    """
    code = models.CharField(max_length=10, unique=True)  # e.g., 'DL', 'UP'
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    
    # Audit fields - automatically managed, read-only in admin
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='geo_state_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='geo_state_updated')
    
    history = HistoricalRecords()
    class Meta:
        ordering = ['name']
    def save(self, *args, **kwargs):
        if self.code: self.code = self.code.strip().upper()
        if self.name: self.name = self.name.strip()
        super().save(*args, **kwargs)
    def __str__(self): return f"{self.name} ({self.code})"

class City(models.Model):
    """
    City master data model.
    
    Audit fields (created_at, updated_at, created_by, updated_by) are automatically
    managed by the system and should not be manually edited.
    """
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='cities')
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    
    # Audit fields - automatically managed, read-only in admin
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='geo_city_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='geo_city_updated')
    
    history = HistoricalRecords()
    class Meta:
        constraints = [models.UniqueConstraint(fields=['state','name'], name='uniq_city_per_state')]
        ordering = ['name']
    def save(self, *args, **kwargs):
        if self.name: self.name = self.name.strip()
        super().save(*args, **kwargs)
    def __str__(self): return f"{self.name}, {self.state.code}"

_pin_validator = RegexValidator(r'^[0-9]{6}$', 'Pincode must be 6 digits')

class Pincode(models.Model):
    """
    Pincode master data model.
    
    Audit fields (created_at, updated_at, created_by, updated_by) are automatically
    managed by the system and should not be manually edited.
    """
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='pincodes')
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='pincodes')
    code = models.CharField(max_length=6, validators=[_pin_validator])
    is_active = models.BooleanField(default=True)
    
    # Audit fields - automatically managed, read-only in admin
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='geo_pin_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='geo_pin_updated')
    
    history = HistoricalRecords()
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code'], name='uniq_pincode_code'),
            models.UniqueConstraint(fields=['city','code'], name='uniq_pincode_per_city')
        ]
        indexes = [models.Index(fields=['state','city','code'])]
        ordering = ['code']
    def clean(self):
        if self.city and self.state and self.city.state_id != self.state_id:
            raise ValidationError('City does not belong to selected State')
    def save(self, *args, **kwargs):
        if self.code: self.code = self.code.strip()
        super().save(*args, **kwargs)
    def __str__(self): return self.code
