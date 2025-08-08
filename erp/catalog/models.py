from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from decimal import Decimal
from simple_history.models import HistoricalRecords


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
