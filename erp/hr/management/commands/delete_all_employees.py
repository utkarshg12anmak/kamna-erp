from django.core.management.base import BaseCommand
from hr.models import Employee

class Command(BaseCommand):
    help = 'Delete all employees from the database'

    def handle(self, *args, **options):
        current_count = Employee.objects.count()
        self.stdout.write(f'Current employees in database: {current_count}')
        
        if current_count > 0:
            self.stdout.write(f'Deleting all {current_count} employees...')
            deleted_count, _ = Employee.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} employees')
            )
        else:
            self.stdout.write(
                self.style.WARNING('No employees found to delete')
            )
        
        remaining_count = Employee.objects.count()
        self.stdout.write(f'Remaining employees: {remaining_count}')
        
        if remaining_count == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ Employee table is now empty!')
            )
