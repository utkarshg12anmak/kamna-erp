from django.db import transaction
from django.utils import timezone
from .models import Employee

def next_emp_code():
    y = timezone.now().year
    prefix = f'EMP-{y}-'
    with transaction.atomic():
        last = (Employee.objects.filter(emp_code__startswith=prefix)
                .order_by('-emp_code')
                .values_list('emp_code', flat=True)
                .first())
        seq = int(last.split('-')[-1]) + 1 if last else 1
        return f'{prefix}{seq:04d}'

def mask_value(field, val):
    if val is None:
        return ''
    s = str(val)
    if field == 'aadhaar_last4':
        return f'****{s}'
    if field == 'pan_number' and len(s) == 10:
        return s[:2] + '***' + s[5:8] + s[8:]
    return s
