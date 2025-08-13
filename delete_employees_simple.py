#!/usr/bin/env python3
"""
Simple script to delete all employees from the database
"""
import os
import sys
import django

# Add the Django project to the path
project_path = '/Users/dealshare/Documents/GitHub/kamna-erp/erp'
if project_path not in sys.path:
    sys.path.append(project_path)

# Change to project directory and set up Django
os.chdir(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')

try:
    django.setup()
    
    # Import the Employee model
    from hr.models import Employee
    
    # Get current count
    current_count = Employee.objects.count()
    print(f"Current employees in database: {current_count}")
    
    if current_count > 0:
        print(f"Deleting all {current_count} employees...")
        
        # Delete all employees
        deleted_count, deletion_info = Employee.objects.all().delete()
        
        print(f"Successfully deleted {deleted_count} employee records")
        
        # Verify deletion
        remaining_count = Employee.objects.count()
        print(f"Remaining employees: {remaining_count}")
        
        if remaining_count == 0:
            print("✅ SUCCESS: Employee table is now empty!")
        else:
            print(f"⚠️ WARNING: {remaining_count} employees still remain")
    else:
        print("Employee table is already empty")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
