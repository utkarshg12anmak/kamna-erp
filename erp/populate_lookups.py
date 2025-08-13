#!/usr/bin/env python3

import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/dealshare/Documents/GitHub/kamna-erp/erp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hr.models import Employee, Department, Designation
from django.utils.text import slugify

def populate_data():
    # Get existing departments and designations
    existing_departments = set()
    existing_designations = set()

    for employee in Employee.objects.all():
        if employee.department and employee.department.strip():
            existing_departments.add(employee.department.strip())
        if employee.designation and employee.designation.strip():
            existing_designations.add(employee.designation.strip())

    print(f'Found {len(existing_departments)} unique departments: {existing_departments}')
    print(f'Found {len(existing_designations)} unique designations: {existing_designations}')

    # Create Department objects
    for dept_name in existing_departments:
        code = slugify(dept_name).upper().replace('-', '_')[:20]
        
        # Ensure unique code
        original_code = code
        counter = 1
        while Department.objects.filter(code=code).exists():
            code = f'{original_code}_{counter}'
            counter += 1
        
        dept, created = Department.objects.get_or_create(
            name=dept_name,
            defaults={
                'code': code,
                'description': f'Department: {dept_name}',
                'is_active': True
            }
        )
        if created:
            print(f'Created Department: {dept_name} (Code: {code})')

    # Create Designation objects
    for desig_name in existing_designations:
        desig, created = Designation.objects.get_or_create(
            title=desig_name,
            defaults={
                'description': f'Designation: {desig_name}',
                'is_active': True
            }
        )
        if created:
            print(f'Created Designation: {desig_name}')

    print(f'\nTotal Departments: {Department.objects.count()}')
    print(f'Total Designations: {Designation.objects.count()}')

if __name__ == '__main__':
    populate_data()
