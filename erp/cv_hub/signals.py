from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import (CvHubEntry, CvHubGSTRegistration, CvHubAddress, CvHubContact,
                     CvHubTaxpayerType)

@receiver(pre_save, sender=CvHubEntry)
def cv_hub_entry_validate(sender, instance, **kwargs):
    if not (instance.is_customer or instance.is_supplier or instance.is_vendor or instance.is_logistics):
        raise ValidationError('Select at least one role (customer/supplier/vendor/logistics)')
    if not (instance.for_sales or instance.for_purchase):
        raise ValidationError('Select at least one of For Sales / For Purchase')

@receiver(pre_save, sender=CvHubGSTRegistration)
def gst_validate(sender, instance, **kwargs):
    if instance.taxpayer_type == CvHubTaxpayerType.UNREGISTERED:
        instance.gstin = None
    else:
        if not instance.gstin or len(instance.gstin.strip()) != 15:
            raise ValidationError('GSTIN must be 15 characters for registered taxpayers')
        instance.gstin = instance.gstin.strip().upper()

@receiver(post_save, sender=CvHubGSTRegistration)
def gst_primary_unique(sender, instance, **kwargs):
    if instance.is_primary:
        CvHubGSTRegistration.objects.filter(entry=instance.entry, is_primary=True).exclude(id=instance.id).update(is_primary=False)

@receiver(post_save, sender=CvHubAddress)
def address_defaults_unique(sender, instance, **kwargs):
    if instance.is_default_billing:
        CvHubAddress.objects.filter(entry=instance.entry, is_default_billing=True).exclude(id=instance.id).update(is_default_billing=False)
    if instance.is_default_shipping:
        CvHubAddress.objects.filter(entry=instance.entry, is_default_shipping=True).exclude(id=instance.id).update(is_default_shipping=False)

@receiver(pre_save, sender=CvHubContact)
def contact_phone_norm(sender, instance, **kwargs):
    if instance.phone:
        instance.phone = instance.phone.replace(' ','').replace('-','')

@receiver(post_save, sender=CvHubContact)
def contact_primary_unique(sender, instance, **kwargs):
    if instance.is_primary:
        CvHubContact.objects.filter(entry=instance.entry, is_primary=True).exclude(id=instance.id).update(is_primary=False)
