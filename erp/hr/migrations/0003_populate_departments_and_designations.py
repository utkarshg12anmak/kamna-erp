from django.db import migrations
from django.utils.text import slugify

def populate_departments_and_designations(apps, schema_editor):
    """
    Populate Department and Designation models from existing Employee data
    """
    Employee = apps.get_model('hr', 'Employee')
    Department = apps.get_model('hr', 'Department')
    Designation = apps.get_model('hr', 'Designation')
    
    # Get existing departments and designations
    existing_departments = set()
    existing_designations = set()
    
    for employee in Employee.objects.all():
        if employee.department and employee.department.strip():
            existing_departments.add(employee.department.strip())
        if employee.designation and employee.designation.strip():
            existing_designations.add(employee.designation.strip())
    
    print(f"Found {len(existing_departments)} unique departments")
    print(f"Found {len(existing_designations)} unique designations")
    
    # Create Department objects
    department_mapping = {}
    for dept_name in existing_departments:
        # Generate a code from the name
        code = slugify(dept_name).upper().replace('-', '_')[:20]
        
        # Ensure unique code
        original_code = code
        counter = 1
        while Department.objects.filter(code=code).exists():
            code = f"{original_code}_{counter}"
            counter += 1
        
        dept, created = Department.objects.get_or_create(
            name=dept_name,
            defaults={
                'code': code,
                'description': f'Department: {dept_name}',
                'is_active': True
            }
        )
        department_mapping[dept_name] = dept
        if created:
            print(f"Created Department: {dept_name} (Code: {code})")
    
    # Create Designation objects
    designation_mapping = {}
    for desig_name in existing_designations:
        desig, created = Designation.objects.get_or_create(
            title=desig_name,
            defaults={
                'description': f'Designation: {desig_name}',
                'is_active': True
            }
        )
        designation_mapping[desig_name] = desig
        if created:
            print(f"Created Designation: {desig_name}")

def reverse_populate_departments_and_designations(apps, schema_editor):
    """
    Reverse migration - delete created departments and designations
    """
    Department = apps.get_model('hr', 'Department')
    Designation = apps.get_model('hr', 'Designation')
    
    Department.objects.all().delete()
    Designation.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('hr', '0002_department_alter_position_options_and_more'),
    ]

    operations = [
        migrations.RunPython(
            populate_departments_and_designations,
            reverse_populate_departments_and_designations
        ),
    ]
