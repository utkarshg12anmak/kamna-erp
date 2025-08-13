from hr.models import Employee
from django.utils import timezone

# Create test employees
employees_data = [
    {
        'emp_code': 'EMP-2025-0001',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@company.com',
        'phone': '+91 9876543210',
        'department': 'Engineering',
        'designation': 'Software Engineer',
        'status': 'ACTIVE',
        'gender': 'MALE'
    },
    {
        'emp_code': 'EMP-2025-0002',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@company.com',
        'phone': '+91 9876543211',
        'department': 'Marketing',
        'designation': 'Marketing Manager',
        'status': 'ACTIVE',
        'gender': 'FEMALE'
    },
    {
        'emp_code': 'EMP-2025-0003',
        'first_name': 'Mike',
        'last_name': 'Johnson',
        'email': 'mike.johnson@company.com',
        'phone': '+91 9876543212',
        'department': 'HR',
        'designation': 'HR Specialist',
        'status': 'ACTIVE',
        'gender': 'MALE'
    }
]

created_count = 0
for emp_data in employees_data:
    try:
        employee, created = Employee.objects.get_or_create(
            emp_code=emp_data['emp_code'],
            defaults={
                **emp_data,
                'date_of_joining': timezone.now().date(),
                'salary_amount': 50000,
                'salary_currency': 'INR',
                'salary_period': 'MONTHLY',
                'is_phone_assigned': False,
                'is_laptop_assigned': False,
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Created: {employee.first_name} {employee.last_name} ({employee.emp_code}) - ID: {employee.id}")
        else:
            print(f"ℹ️  Exists: {employee.first_name} {employee.last_name} ({employee.emp_code}) - ID: {employee.id}")
            
    except Exception as e:
        print(f"❌ Error creating {emp_data['emp_code']}: {e}")

total_employees = Employee.objects.count()
print(f"\n📊 Summary:")
print(f"   New employees created: {created_count}")
print(f"   Total employees in database: {total_employees}")

if total_employees > 0:
    print(f"\n🆔 Employee IDs for testing:")
    for emp in Employee.objects.all().order_by('emp_code'):
        print(f"   ID {emp.id}: {emp.first_name} {emp.last_name} ({emp.emp_code})")

print(f"\n🎉 Test employees ready!")
