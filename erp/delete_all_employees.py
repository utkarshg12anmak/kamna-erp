#!/usr/bin/env python3
"""
Script to safely delete all employees from the database
"""
import os
import sys
import django

# Set up Django environment
project_path = '/Users/dealshare/Documents/GitHub/kamna-erp/erp'
sys.path.insert(0, project_path)
os.chdir(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')

# Setup Django
django.setup()

def delete_all_employees():
    """Delete all employees from the database"""
    from hr.models import Employee
    
    # Show current count
    current_count = Employee.objects.count()
    print(f'📊 Current employee count: {current_count}')
    
    if current_count > 0:
        print('\n👥 Employees to be deleted:')
        for i, emp in enumerate(Employee.objects.all()[:5], 1):
            print(f'  {i}. {emp.emp_code}: {emp.first_name} {emp.last_name} ({emp.email})')
        
        if current_count > 5:
            print(f'  ... and {current_count - 5} more employees')
        
        # Ask for confirmation (in script, we'll proceed)
        print(f'\n🗑️ Proceeding to delete all {current_count} employees...')
        
        # Delete all employees
        deleted_count, deletion_details = Employee.objects.all().delete()
        print(f'\n✅ Successfully deleted {deleted_count} employee records')
        
        # Show deletion details
        if deletion_details:
            print('\n📋 Deletion details:')
            for model, count in deletion_details.items():
                print(f'  - {model}: {count} records')
        
        # Verify deletion
        remaining_count = Employee.objects.count()
        print(f'\n📊 Remaining employee count: {remaining_count}')
        
        if remaining_count == 0:
            print('🎉 Employee table is now completely empty!')
        else:
            print(f'⚠️ Warning: {remaining_count} employees still remain')
            
        return True
    else:
        print('ℹ️ Employee table is already empty - nothing to delete')
        return False

if __name__ == "__main__":
    print("🗑️ Employee Database Cleanup Script")
    print("=" * 40)
    
    try:
        success = delete_all_employees()
        
        if success:
            print("\n" + "=" * 40)
            print("✅ CLEANUP COMPLETE")
            print("🔄 You can now test the employee form with a clean database")
            print("📝 Create new employees at: http://localhost:8000/app/hr/employees/new")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
