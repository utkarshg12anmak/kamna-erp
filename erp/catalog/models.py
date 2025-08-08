from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from decimal import Decimal
from simple_history.models import HistoricalRecords
import string
import random


def generate_unique_sku():
    chars = string.ascii_uppercase + string.digits
    for _ in range(100):  # retry up to 100 times
        candidate = ''.join(random.choices(chars, k=10))
        if not Item.objects.filter(sku=candidate).exists():
            return candidate
    raise RuntimeError("Failed to generate unique SKU after many attempts")


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="brand_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="brand_updated",
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"parent__isnull": True},
        related_name="children",
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category_updated",
    )
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "parent"], name="uniq_category_name_per_parent"),
        ]

    def clean(self):
        super().clean()
        if self.parent:
            if self.parent_id == self.id:
                raise ValidationError({"parent": "Category cannot be its own parent."})
            if self.parent.parent_id is not None:
                raise ValidationError({"parent": "Only one level of depth is allowed (parent must be a root category)."})

    def __str__(self):
        return self.name


class TaxRate(models.Model):
    name = models.CharField(max_length=50, unique=True)
    percent = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))])
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="taxrate_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="taxrate_updated",
    )
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.name} ({self.percent}%)"


class UoM(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50, unique=True)
    ratio_to_base = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal("1.0"))
    base = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uom_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uom_updated",
    )
    history = HistoricalRecords()

    def clean(self):
        super().clean()
        if self.ratio_to_base is None or Decimal(self.ratio_to_base) <= Decimal("0"):
            raise ValidationError({"ratio_to_base": "Ratio to base must be greater than 0."})

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.upper()
        self.full_clean(exclude=None)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Item(models.Model):
    PRODUCT_TYPE_CHOICES = (
        ("GOODS", "GOODS"),
        ("SERVICE", "SERVICE"),
    )
    STATUS_CHOICES = (
        ("ACTIVE", "ACTIVE"),
        ("DRAFT", "DRAFT"),
        ("ARCHIVED", "ARCHIVED"),
    )

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=10, unique=True, editable=False, db_index=True)
    product_type = models.CharField(max_length=8, choices=PRODUCT_TYPE_CHOICES, default="GOODS")
    brand = models.ForeignKey('Brand', null=True, blank=True, on_delete=models.SET_NULL, related_name='items')
    category = models.ForeignKey('Category', null=True, blank=True, on_delete=models.SET_NULL, related_name='items')
    uom = models.ForeignKey('UoM', null=True, blank=True, on_delete=models.SET_NULL, related_name='items')
    tax_rate = models.ForeignKey('TaxRate', null=True, blank=True, on_delete=models.SET_NULL, related_name='items')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="DRAFT")
    for_sales = models.BooleanField(default=False)
    for_purchase = models.BooleanField(default=False)
    for_manufacture = models.BooleanField(default=False)
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='item_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='item_updated')
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["brand"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status"]),
            models.Index(fields=["for_sales"]),
            models.Index(fields=["for_purchase"]),
            models.Index(fields=["for_manufacture"]),
        ]
        ordering = ["name"]

    def clean(self):
        super().clean()
        # Ensure SKU uppercase if present
        if self.sku:
            self.sku = self.sku.upper()
        # Category rules
        if self.product_type == "GOODS":
            if not self.category or not getattr(self.category, 'parent_id', None):
                raise ValidationError({"category": "GOODS must have a child category (category with a parent)."})
            if not self.uom_id:
                raise ValidationError({"uom": "UoM is required for GOODS."})
        else:  # SERVICE
            if self.category and self.category.parent_id is None:
                raise ValidationError({"category": "If provided, category must be a child category."})

    def save(self, *args, **kwargs):
        # SKU generation on create only
        if not self.pk and not self.sku:
            self.sku = generate_unique_sku()
        self.full_clean(exclude=None)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"
