from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from hr.models import Employee, AccessProfile, EmploymentStatus

class Command(BaseCommand):
    help = "HR smoke test: create, update, soft delete employee"

    def handle(self, *args, **options):
        User = get_user_model()
        emp = Employee.objects.create(
            first_name='Smoke',
            phone='9999999999',
            date_of_joining=timezone.now().date(),
            salary_amount=0,
        )
        emp.pan_number = 'ABCDE1234F'
        emp.aadhaar_last4 = '1234'
        emp.save()
        ap, _ = AccessProfile.objects.get_or_create(name='Basic', defaults={'description':'Basic access'})
        emp.access_profile = ap
        emp.save(update_fields=['access_profile'])
        emp.status = EmploymentStatus.EXITED
        emp.save(update_fields=['status'])
        self.stdout.write('HR_SMOKE_OK')
