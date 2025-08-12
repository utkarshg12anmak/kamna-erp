from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Employee, OrgUnit
from .utils import next_emp_code

@receiver(pre_save, sender=Employee)
def employee_presave(sender, instance, **kwargs):
    if not instance.emp_code:
        instance.emp_code = next_emp_code()
    if instance.pan_number:
        instance.pan_number = instance.pan_number.upper()
    if instance.manager_id and instance.manager_id == instance.id:
        raise ValidationError('Manager cannot be self')
    # simple cycle guard (deep checks can be added):
    m = instance.manager
    seen = set([instance.id])
    while m:
        if m.id in seen:
            raise ValidationError('Manager cycle detected')
        seen.add(m.id)
        m = m.manager

@receiver(pre_save, sender=OrgUnit)
def orgunit_presave(sender, instance, **kwargs):
    if instance.parent_id:
        seen = set([instance.id])
        p = instance.parent
        while p:
            if p.id in seen:
                raise ValidationError('OrgUnit cycle detected')
            seen.add(p.id)
            p = p.parent
