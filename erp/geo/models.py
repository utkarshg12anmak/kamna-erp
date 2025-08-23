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


# Territory feature models
TERRITORY_TYPES = (
    ('STATE', 'STATE'),
    ('CITY', 'CITY'),
    ('PINCODE', 'PINCODE'),
)


class Territory(models.Model):
    """
    Territory master data model for grouping geo entities.
    
    Audit fields (created_at, updated_at, created_by, updated_by) are automatically
    managed by the system and should not be manually edited.
    """
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=10, choices=TERRITORY_TYPES)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_till = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Audit fields - automatically managed, read-only in admin
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='geo_territory_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='geo_territory_updated')
    
    history = HistoricalRecords()
    
    class Meta:
        indexes = [
            models.Index(fields=['type', 'is_active']), 
            models.Index(fields=['effective_from', 'effective_till'])
        ]
        ordering = ['code']
        verbose_name_plural = 'territories'
    
    def clean(self):
        if self.code: 
            self.code = self.code.strip().upper()
        if self.name: 
            self.name = self.name.strip()
        if self.effective_from and self.effective_till and self.effective_till < self.effective_from:
            raise ValidationError({'effective_till': 'effective_till must be on/after effective_from'})
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self): 
        return f"{self.code} ({self.type})"


class TerritoryMember(models.Model):
    """
    Membership relationship between Territory and geo entities.
    Territory type determines which geo entity can be added as member.
    """
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE, related_name='members')
    state = models.ForeignKey('State', null=True, blank=True, on_delete=models.PROTECT)
    city = models.ForeignKey('City', null=True, blank=True, on_delete=models.PROTECT)
    pincode = models.ForeignKey('Pincode', null=True, blank=True, on_delete=models.PROTECT)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['territory', 'state'], name='uniq_state_member_per_territory'),
            models.UniqueConstraint(fields=['territory', 'city'], name='uniq_city_member_per_territory'),
            models.UniqueConstraint(fields=['territory', 'pincode'], name='uniq_pincode_member_per_territory'),
        ]
        indexes = [models.Index(fields=['territory'])]
        verbose_name = 'territory member'
        verbose_name_plural = 'territory members'
    
    def clean(self):
        t = self.territory
        if not t: 
            return
        
        filled = [bool(self.state), bool(self.city), bool(self.pincode)]
        if sum(filled) != 1:
            raise ValidationError('Provide exactly one of state/city/pincode based on Territory.type')
        
        if t.type == 'STATE' and not self.state:
            raise ValidationError({'state': 'Territory type STATE requires state; city/pincode must be empty'})
        if t.type == 'CITY' and not self.city:
            raise ValidationError({'city': 'Territory type CITY requires city; state/pincode must be empty'})
        if t.type == 'PINCODE' and not self.pincode:
            raise ValidationError({'pincode': 'Territory type PINCODE requires pincode; state/city must be empty'})
        
        if self.state and not self.state.is_active:
            raise ValidationError({'state': 'Cannot add INACTIVE State as member'})
        if self.city and not self.city.is_active:
            raise ValidationError({'city': 'Cannot add INACTIVE City as member'})
        if self.pincode and not self.pincode.is_active:
            raise ValidationError({'pincode': 'Cannot add INACTIVE Pincode as member'})
    
    def __str__(self):
        if self.state: 
            return f"STATE:{self.state.code}"
        if self.city: 
            return f"CITY:{self.city.name}"
        if self.pincode: 
            return f"PIN:{self.pincode.code}"
        return '<member>'


class TerritoryCoverage(models.Model):
    territory = models.ForeignKey('geo.Territory', on_delete=models.CASCADE, related_name='coverage')
    pincode = models.ForeignKey('geo.Pincode', on_delete=models.PROTECT)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['territory','pincode'], name='uniq_territory_pincode_coverage')]
        indexes = [models.Index(fields=['territory']), models.Index(fields=['pincode'])]
        verbose_name = 'Territory Coverage'
        verbose_name_plural = 'Territory Coverage'
