"""
Cascade deactivation signals for geo models.

When a State is deactivated, all its Cities and Pincodes are deactivated.
When a City is deactivated, all its Pincodes are deactivated.
This is one-way cascade (deactivation only).
"""
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import State, City, Pincode, TerritoryMember
from .services import rebuild_territory_coverage


@receiver(pre_save, sender=State)
def state_pre_save(sender, instance: State, **kwargs):
    """Capture previous is_active state before save."""
    if instance.pk:
        try:
            old_instance = State.objects.get(pk=instance.pk)
            instance._old_is_active = old_instance.is_active
        except State.DoesNotExist:
            instance._old_is_active = None
    else:
        instance._old_is_active = None


@receiver(post_save, sender=State)
def state_cascade_deactivation(sender, instance: State, created, **kwargs):
    """Cascade deactivation from State to Cities and Pincodes."""
    if created:
        return
    
    # Check if state was deactivated
    old_is_active = getattr(instance, '_old_is_active', None)
    if old_is_active and not instance.is_active:
        # Deactivate all cities in this state
        City.objects.filter(state=instance, is_active=True).update(is_active=False)
        # Deactivate all pincodes in this state
        Pincode.objects.filter(state=instance, is_active=True).update(is_active=False)


@receiver(pre_save, sender=City)
def city_pre_save(sender, instance: City, **kwargs):
    """Capture previous is_active state before save."""
    if instance.pk:
        try:
            old_instance = City.objects.get(pk=instance.pk)
            instance._old_is_active = old_instance.is_active
        except City.DoesNotExist:
            instance._old_is_active = None
    else:
        instance._old_is_active = None


@receiver(post_save, sender=City)
def city_cascade_deactivation(sender, instance: City, created, **kwargs):
    """Cascade deactivation from City to Pincodes."""
    if created:
        return
    
    # Check if city was deactivated
    old_is_active = getattr(instance, '_old_is_active', None)
    if old_is_active and not instance.is_active:
        # Deactivate all pincodes in this city
        Pincode.objects.filter(city=instance, is_active=True).update(is_active=False)


# Territory signals
@receiver(pre_save, sender='geo.Territory')
def prevent_type_change_with_members(sender, instance, **kwargs):
    """Prevent Territory.type changes after members have been added."""
    if not instance.pk:
        return
    
    try:
        prev = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    
    if prev.type != instance.type and prev.members.exists():
        from django.core.exceptions import ValidationError
        raise ValidationError('Cannot change Territory.type after members have been added')


# Territory Coverage signals
@receiver(post_save, sender=TerritoryMember)
def _tm_saved(sender, instance, created, **kwargs):
    rebuild_territory_coverage(instance.territory_id)

@receiver(post_delete, sender=TerritoryMember)
def _tm_deleted(sender, instance, **kwargs):
    rebuild_territory_coverage(instance.territory_id)
