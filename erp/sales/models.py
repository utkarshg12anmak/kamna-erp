from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

class PriceListStatus(models.TextChoices):
    DRAFT='DRAFT','Draft'; PUBLISHED='PUBLISHED','Published'; ARCHIVED='ARCHIVED','Archived'

class PriceList(models.Model):
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    territory = models.ForeignKey('geo.Territory', on_delete=models.PROTECT, related_name='sales_price_lists')
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=10, choices=PriceListStatus.choices, default=PriceListStatus.DRAFT)
    effective_from = models.DateField(null=True, blank=True)
    effective_till = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='pl_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='pl_updated')
    history = HistoricalRecords()
    class Meta:
        indexes=[models.Index(fields=['territory','status']), models.Index(fields=['effective_from','effective_till'])]
        ordering=['code']
    def clean(self):
        if self.code: self.code=self.code.strip().upper()
        if self.name: self.name=self.name.strip()
        if self.currency!='INR': raise ValidationError({'currency':'Only INR allowed'})
        if self.effective_from and self.effective_till and self.effective_till < self.effective_from:
            raise ValidationError({'effective_till':'must be on/after effective_from'})
    def __str__(self): return f"{self.code} ({self.status})"

class PriceListItem(models.Model):
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('catalog.Item', on_delete=models.PROTECT)

    def clean(self):
        # Conflict check: prevent same item in overlapping lists for same territory and status
        from .models import PriceCoverage, PriceListStatus
        if self.price_list_id and self.item_id:
            pl = self.price_list
            pins = pl.territory.coverage.values_list('pincode_id', flat=True)
            # Only consider DRAFT or PUBLISHED (not ARCHIVED)
            qs = PriceCoverage.objects.filter(
                item_id=self.item_id,
                pincode_id__in=pins,
                status__in=[PriceListStatus.DRAFT, PriceListStatus.PUBLISHED]
            ).exclude(price_list_id=pl.id)
            for pc in qs:
                # Overlap check
                a0, a1 = pl.effective_from, pl.effective_till
                b0, b1 = pc.effective_from, pc.effective_till
                if (a1 or a0) and (b1 or b0):
                    # If windows overlap
                    if not ((a1 and b0 and a1 < b0) or (b1 and a0 and b1 < a0)):
                        # Only block if the other price list is not archived
                        if pc.price_list.status in [PriceListStatus.DRAFT, PriceListStatus.PUBLISHED]:
                            raise ValidationError({'item': f'Conflicts with existing price list(s): {pc.price_list.code}'})
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        from .services import sync_pricelist_coverage
        sync_pricelist_coverage(self.price_list_id)

    def delete(self, *args, **kwargs):
        price_list_id = self.price_list_id
        super().delete(*args, **kwargs)
        from .services import sync_pricelist_coverage
        sync_pricelist_coverage(price_list_id)

    class Meta:
        constraints=[models.UniqueConstraint(fields=['price_list','item'], name='uniq_item_per_pricelist')]

class PriceListTier(models.Model):
    price_list_item = models.ForeignKey('sales.PriceListItem', on_delete=models.CASCADE, related_name='tiers')
    max_qty = models.PositiveIntegerField(null=True, blank=True, help_text='Applies up to and including this quantity; leave empty if open-ended')
    min_unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    is_open_ended = models.BooleanField(default=False)

    class Meta:
        constraints = [
            # Prevent two identical max_qty values within same item
            models.UniqueConstraint(fields=['price_list_item','max_qty'], name='uniq_till_qty_per_item'),
            # Only one open-ended tier per item (partial unique)
            models.UniqueConstraint(fields=['price_list_item','is_open_ended'], name='uniq_open_ended_per_item', condition=models.Q(is_open_ended=True)),
            # If open-ended, max_qty must be NULL; if not open-ended, max_qty must NOT be NULL
            models.CheckConstraint(check=(models.Q(is_open_ended=True, max_qty__isnull=True) | models.Q(is_open_ended=False, max_qty__isnull=False)), name='ck_openended_requires_null_maxqty')
        ]
        ordering = ['max_qty']

    def clean(self):
        # Basic field-level rules
        if self.is_open_ended:
            if self.max_qty is not None:
                raise ValidationError({'max_qty': 'Open-ended tiers must not have max_qty.'})
        else:
            if self.max_qty is None or self.max_qty < 1:
                raise ValidationError({'max_qty': 'max_qty must be >= 1 for non open-ended tiers.'})

        # Sibling rules
        if self.price_list_item_id:
            siblings = self.price_list_item.tiers.exclude(pk=self.pk)
            # Enforce strictly increasing max_qty among non-open-ended tiers
            if not self.is_open_ended and siblings.filter(is_open_ended=False, max_qty=self.max_qty).exists():
                raise ValidationError({'max_qty': 'Duplicate max_qty not allowed for the same item.'})
            # Open-ended must be the last: if any sibling is open-ended and this is not open-ended -> block
            if not self.is_open_ended and siblings.filter(is_open_ended=True).exists():
                raise ValidationError('Cannot add non open-ended tier after an open-ended tier. Open-ended must be the final tier.')
            # If this is open-ended, ensure there is no higher-tier after it (implicit via rule above) — also enforce only one via DB constraint

    def __str__(self):
        return f"<= {self.max_qty if self.max_qty is not None else '∞'} : INR {self.min_unit_price}"

class PriceCoverage(models.Model):
    item = models.ForeignKey('catalog.Item', on_delete=models.CASCADE)
    pincode = models.ForeignKey('geo.Pincode', on_delete=models.CASCADE)
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='coverage_rows')
    effective_from = models.DateField(null=True, blank=True)
    effective_till = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=PriceListStatus.choices)
    class Meta:
        indexes=[models.Index(fields=['item','pincode']), models.Index(fields=['status'])]
