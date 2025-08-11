from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
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


class PhysicalSubtype(models.TextChoices):
    STORAGE = "STORAGE", "STORAGE"


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
    # Include STORAGE as default subtype for PHYSICAL; virtual bins remain as before
    subtype = models.CharField(
        max_length=20,
        choices=PhysicalSubtype.choices + VirtualSubtype.choices,
        null=True,
        blank=True,
    )
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
            # Default subtype to STORAGE for PHYSICAL
            if not self.subtype:
                self.subtype = PhysicalSubtype.STORAGE
            elif self.subtype != PhysicalSubtype.STORAGE:
                raise ValidationError({"subtype": "PHYSICAL locations must have subtype STORAGE"})
        elif self.type == LocationType.VIRTUAL:
            if not self.subtype:
                raise ValidationError({"subtype": "Subtype is required for VIRTUAL locations"})
            if self.subtype == PhysicalSubtype.STORAGE:
                raise ValidationError({"subtype": "VIRTUAL locations cannot use STORAGE subtype"})
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

    def save(self, *args, **kwargs):
        # Enforce default subtype for PHYSICAL at the model level
        if self.type == LocationType.PHYSICAL and not self.subtype:
            self.subtype = PhysicalSubtype.STORAGE
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name or f"{self.type}:{self.subtype or self.code}"


# New: MovementType and StockLedger (append-only)
class MovementType(models.TextChoices):
    ADJ_REQ_DAMAGE = "ADJ_REQ_DAMAGE", "Adj Req Damage"
    ADJ_REQ_LOST = "ADJ_REQ_LOST", "Adj Req Lost"
    ADJ_REQ_EXCESS = "ADJ_REQ_EXCESS", "Adj Req Excess"
    ADJ_APPROVE_DAMAGE = "ADJ_APPROVE_DAMAGE", "Adj Approve Damage"
    ADJ_DECLINE_DAMAGE = "ADJ_DECLINE_DAMAGE", "Adj Decline Damage"
    ADJ_APPROVE_LOST = "ADJ_APPROVE_LOST", "Adj Approve Lost"
    ADJ_DECLINE_LOST = "ADJ_DECLINE_LOST", "Adj Decline Lost"
    ADJ_APPROVE_EXCESS = "ADJ_APPROVE_EXCESS", "Adj Approve Excess"
    # New: decline of EXCESS should post out from EXCESS_PENDING to null
    ADJ_DECLINE_EXCESS = "ADJ_DECLINE_EXCESS", "Adj Decline Excess"
    # New: Putaway movements (from Return/Receive to Physical or to Lost)
    PUTAWAY = "PUTAWAY", "Putaway"
    PUTAWAY_LOST = "PUTAWAY_LOST", "Putaway Lost"
    TRANSFER = "TRANSFER", "Transfer"
    # New: Deletion of a REQUESTED adjustment (revert request postings)
    ADJ_DELETE_REQUEST = "ADJ_DELETE_REQUEST", "Adj Delete Request"


class StockLedger(models.Model):
    ts = models.DateTimeField(auto_now_add=True, db_index=True)
    warehouse = models.ForeignKey("Warehouse", on_delete=models.PROTECT, related_name="+")
    location = models.ForeignKey("Location", on_delete=models.PROTECT, related_name="+")
    item = models.ForeignKey("catalog.Item", on_delete=models.PROTECT, related_name="+")
    qty_delta = models.DecimalField(max_digits=12, decimal_places=3)  # +in, -out
    movement_type = models.CharField(max_length=32, choices=MovementType.choices)
    ref_model = models.CharField(max_length=50, blank=True)
    ref_id = models.CharField(max_length=50, blank=True)
    memo = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["warehouse", "item"]),
            models.Index(fields=["warehouse", "location"]),
            models.Index(fields=["movement_type", "ts"]),
        ]
        verbose_name = "Stock Ledger Entry"
        verbose_name_plural = "Stock Ledger"

    def __str__(self):
        return f"{self.ts} {self.item_id} @ {self.location_id} {self.qty_delta}"


# New: Adjustment workflow
class AdjustmentType(models.TextChoices):
    DAMAGE = "DAMAGE", "DAMAGE"
    LOST = "LOST", "LOST"
    EXCESS = "EXCESS", "EXCESS"


class AdjustmentStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "REQUESTED"
    APPROVED = "APPROVED", "APPROVED"
    DECLINED = "DECLINED", "DECLINED"


class AdjustmentRequest(models.Model):
    number = models.CharField(max_length=20, unique=True, editable=False)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="adjustment_requests")
    type = models.CharField(max_length=10, choices=AdjustmentType.choices)
    item = models.ForeignKey("catalog.Item", on_delete=models.PROTECT, related_name="+")
    source_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    qty = models.DecimalField(max_digits=12, decimal_places=3)
    status = models.CharField(max_length=10, choices=AdjustmentStatus.choices, default=AdjustmentStatus.REQUESTED)
    memo = models.TextField(blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="adj_requested")
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="adj_approved")
    approved_at = models.DateTimeField(null=True, blank=True)
    declined_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="adj_declined")
    declined_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["warehouse", "status"]),
            models.Index(fields=["requested_at"]),
        ]

    def clean(self):
        if self.qty is None or self.qty <= 0:
            raise ValidationError({"qty": "Quantity must be > 0"})
        if self.type in (AdjustmentType.DAMAGE, AdjustmentType.LOST):
            if not self.source_location or self.source_location.type != LocationType.PHYSICAL:
                raise ValidationError({"source_location": "Physical source location required"})
        if self.type == AdjustmentType.EXCESS and self.source_location is not None:
            raise ValidationError({"source_location": "Must be empty for EXCESS"})

    def save(self, *args, **kwargs):
        if not self.number:
            prefix = f"AR-{timezone.now().year}-"
            last = (
                AdjustmentRequest.objects.filter(number__startswith=prefix)
                .order_by("-id")
                .first()
            )
            seq = 1
            if last:
                try:
                    seq = int((last.number or "").split("-")[-1]) + 1
                except Exception:
                    seq = 1
            self.number = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number or f"AR? ({self.type})"
