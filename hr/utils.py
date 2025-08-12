from django.db import transaction
from django.utils import timezone
from .models import Employee

def next_emp_code():
    y = timezone.now().year
    prefix = f'EMP-{y}-'
    with transaction.atomic():
        last = (Employee.objects.filter(emp_code__startswith=prefix)
                .order_by('-emp_code').values_list('emp_code', flat=True).first())
        seq = int(last.split('-')[-1]) + 1 if last else 1
        return f'{prefix}{seq:04d}'
