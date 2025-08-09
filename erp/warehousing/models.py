from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords


class WarehouseStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "ACTIVE"
    INACTIVE = "INACTIVE", "INACTIVE"


class LocationType(models.TextChoices):
    PHYSICAL = "PHYSICAL", "PHYSICAL"
    VIRTUAL = "VIRTUAL", "VIRTUAL"


class VirtualSubtype(models.TextChoices):
    RECEIVE = "RECEIVE", "RECEIVE"
    DISPATCH = "DISPATCH", "DISPATCH"
    RETURN = "RETURN", "RETURN"
    QC = "QC", "QC"
    HOLD = "HOLD", "HOLD"
    DAMAGE = "DAMAGE", "DAMAGE"
    LOST = "LOST", "LOST"
    EXCESS = "EXCESS", "EXCESS"
    LOST_PENDING = "LOST_PENDING", "LOST_PENDING"
    EXCESS_PENDING = "EXCESS_PENDING", "EXCESS_PENDING"
    DAMAGE_PENDING = "DAMAGE_PENDING", "DAMAGE_PENDING"


class Warehouse(models.Model):
    # Natural id, default set by DB sequence via migration
    warehouse_id = models.PositiveIntegerField(unique=True, editable=False, db_index=True, null=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    status = models.CharField(max_length=10, choices=WarehouseStatus.choices, default=WarehouseStatus.ACTIVE)
    gstin = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=180, blank=True)
    address_line2 = models.CharField(max_length=180, blank=True)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    pincode = models.CharField(max_length=12)
    country = models.CharField(max_length=80, default="India")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="warehouses_created")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="warehouses_updated")
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["city"]),
            models.Index(fields=["state"]),
        ]
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"

    def clean(self):
        # Validate GSTIN (India: 15 alphanumeric uppercase)
        gstin_validator = RegexValidator(regex=r"^[0-9A-Z]{15}$", message="Invalid GSTIN; must be 15 chars (A-Z, 0-9)")
        gstin_validator(self.gstin)
        # Lat/Long ranges
        if not (-90 <= float(self.latitude) <= 90):
            raise ValidationError({"latitude": "Latitude must be between -90 and 90"})
        if not (-180 <= float(self.longitude) <= 180):
            raise ValidationError({"longitude": "Longitude must be between -180 and 180"})

    def save(self, *args, **kwargs):
        # Leave warehouse_id to DB default sequence; ensure not manually set to 0/None incorrectly
        if self.warehouse_id is None:
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Location(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="locations")
    type = models.CharField(max_length=8, choices=LocationType.choices)
    subtype = models.CharField(max_length=20, choices=VirtualSubtype.choices, null=True, blank=True)
    display_name = models.CharField(max_length=120, blank=True)
    code = models.CharField(max_length=32, blank=True)
    system_managed = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=WarehouseStatus.choices, default=WarehouseStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="locations_created")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="locations_updated")
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "code"],
                name="uq_location_code_per_wh",
                condition=Q(type=LocationType.PHYSICAL),
            )
        ]
        indexes = [
            models.Index(fields=["warehouse"]),
            models.Index(fields=["status"]),
            models.Index(fields=["type"]),
            models.Index(fields=["subtype"]),
        ]
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def clean(self):
        if self.type == LocationType.PHYSICAL:
            if not self.display_name:
                raise ValidationError({"display_name": "Display name is required for PHYSICAL locations"})
            if not self.code:
                raise ValidationError({"code": "Code is required for PHYSICAL locations"})
        elif self.type == LocationType.VIRTUAL:
            if not self.subtype:
                raise ValidationError({"subtype": "Subtype is required for VIRTUAL locations"})
        else:
            raise ValidationError({"type": "Invalid location type"})

        if self.system_managed and self.pk:
            # Prevent renaming system-managed fields
            orig = Location.objects.get(pk=self.pk)
            immutable_fields_changed = (
                (orig.code != self.code)
                or (orig.display_name != self.display_name)
                or (orig.subtype != self.subtype)
            )
            if immutable_fields_changed:
                raise ValidationError("System-managed locations cannot be renamed")

    def __str__(self):
        return self.display_name or f"{self.type}:{self.subtype or self.code}"
