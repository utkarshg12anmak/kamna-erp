from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Employee
from .utils import next_emp_code

@receiver(pre_save, sender=Employee)
def employee_presave(sender, instance, **kwargs):
    if not instance.emp_code:
        instance.emp_code = next_emp_code()
    if instance.pan_number:
        instance.pan_number = instance.pan_number.upper()
    if instance.manager_id and instance.manager_id == instance.id:
        raise ValidationError('Manager cannot be self')
