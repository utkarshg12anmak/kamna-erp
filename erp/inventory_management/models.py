from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


class STNStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    CREATED = 'CREATED', 'Created'
    DISPATCHED = 'DISPATCHED', 'Dispatched'
    RECEIVED = 'RECEIVED', 'Received'
    DELETED = 'DELETED', 'Deleted'


class STN(models.Model):
    stn_code = models.CharField(max_length=20, unique=True, blank=True)
    source_warehouse = models.ForeignKey('warehousing.Warehouse', on_delete=models.PROTECT, related_name='stns_source')
    destination_warehouse = models.ForeignKey('warehousing.Warehouse', on_delete=models.PROTECT, related_name='stns_destination')
    status = models.CharField(max_length=12, choices=STNStatus.choices, default=STNStatus.DRAFT)
    notes = models.TextField(blank=True)
    sum_created_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    sum_dispatched_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    sum_received_qty = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='stns_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='stns_updated')
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['source_warehouse', 'destination_warehouse'])
        ]

    def __str__(self):
        return self.stn_code or f'STN#{self.id}'


class STNDetail(models.Model):
    stn = models.ForeignKey(STN, on_delete=models.CASCADE, related_name='lines')
    sku = models.ForeignKey('catalog.Item', on_delete=models.PROTECT)
    created_qty = models.DecimalField(max_digits=14, decimal_places=3)
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['stn', 'sku'], name='unique_sku_per_stn')
        ]


class STNStatusHistory(models.Model):
    stn = models.ForeignKey(STN, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=12, choices=STNStatus.choices, null=True, blank=True)
    to_status = models.CharField(max_length=12, choices=STNStatus.choices)
    reason = models.CharField(max_length=200, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
