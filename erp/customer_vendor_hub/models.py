from __future__ import annotations
from django.db import models
from simple_history.models import HistoricalRecords
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Q


class State(models.Model):
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=64)
    country = models.CharField(max_length=64, default="India")
    history = HistoricalRecords()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class City(models.Model):
    name = models.CharField(max_length=64)
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="cities")
    history = HistoricalRecords()

    class Meta:
        unique_together = ("name", "state")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.state.code}"


class Partner(models.Model):
    class PartnerType(models.TextChoices):
        COMPANY = "COMPANY", "Company"
        INDIVIDUAL = "INDIVIDUAL", "Individual"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    name = models.CharField(max_length=128)
    type = models.CharField(max_length=16, choices=PartnerType.choices, default=PartnerType.COMPANY)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    # Roles
    is_customer = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_carrier = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False)

    # Basic metadata
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


GSTIN_REGEX = RegexValidator(
    regex=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$",
    message="Invalid GSTIN format",
)


class GSTRegistration(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="gst_regs")
    gstin = models.CharField(max_length=15, validators=[GSTIN_REGEX])
    legal_name = models.CharField(max_length=128)
    trade_name = models.CharField(max_length=128, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        unique_together = ("partner", "gstin")
        constraints = [
            models.UniqueConstraint(
                fields=["partner"],
                condition=Q(is_default=True),
                name="uniq_default_gst_per_partner",
            )
        ]

    def clean(self):
        # Toggle default uniqueness per partner (application-level guard)
        if self.is_default:
            qs = GSTRegistration.objects.filter(partner=self.partner, is_default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"is_default": "Only one default GST registration is allowed per partner"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.partner.name} - {self.gstin}"


class Address(models.Model):
    class AddressType(models.TextChoices):
        BILLING = "BILLING", "Billing"
        SHIPPING = "SHIPPING", "Shipping"
        OTHER = "OTHER", "Other"

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="addresses")
    type = models.CharField(max_length=16, choices=AddressType.choices, default=AddressType.SHIPPING)
    line1 = models.CharField(max_length=128)
    line2 = models.CharField(max_length=128, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="addresses")
    postal_code = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True,
                                   validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True,
                                    validators=[MinValueValidator(-180), MaxValueValidator(180)])
    is_primary = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        ordering = ["partner__name", "type", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["partner"],
                condition=Q(is_primary=True),
                name="uniq_primary_address_per_partner",
            )
        ]

    def clean(self):
        # City belongs to state check implicit via FK; additional rules could be added
        if self.is_primary:
            qs = Address.objects.filter(partner=self.partner, is_primary=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"is_primary": "Only one primary address is allowed per partner"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.partner.name} - {self.line1}, {self.city.name}"


class Contact(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=128)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        ordering = ["partner__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["partner"],
                condition=Q(is_primary=True),
                name="uniq_primary_contact_per_partner",
            )
        ]

    def clean(self):
        if self.is_primary:
            qs = Contact.objects.filter(partner=self.partner, is_primary=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"is_primary": "Only one primary contact is allowed per partner"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.partner.name} - {self.name}"
