from hr.models import Employee, Department, Designation
from django.utils.text import slugify

# Get existing departments and designations
existing_departments = set()
existing_designations = set()

for employee in Employee.objects.all():
    if employee.department and employee.department.strip():
        existing_departments.add(employee.department.strip())
    if employee.designation and employee.designation.strip():
        existing_designations.add(employee.designation.strip())

print(f'Found {len(existing_departments)} unique departments')
print(f'Found {len(existing_designations)} unique designations')

# Create Department objects
for dept_name in existing_departments:
    code = slugify(dept_name).upper().replace('-', '_')[:20]
    
    dept, created = Department.objects.get_or_create(
        name=dept_name,
        defaults={
            'code': code,
            'description': f'Department: {dept_name}',
            'is_active': True
        }
    )
    print(f'Department {dept_name}: {"created" if created else "already exists"}')

# Create Designation objects
for desig_name in existing_designations:
    desig, created = Designation.objects.get_or_create(
        title=desig_name,
        defaults={
            'description': f'Designation: {desig_name}',
            'is_active': True
        }
    )
    print(f'Designation {desig_name}: {"created" if created else "already exists"}')

print(f'Final count - Departments: {Department.objects.count()}, Designations: {Designation.objects.count()}')
