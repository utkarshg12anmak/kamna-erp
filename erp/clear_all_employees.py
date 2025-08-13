#!/usr/bin/env python3
"""
Django Management Command to Clear All Employees
Run this with: python manage.py shell < clear_all_employees.py
"""

print("🗑️ Clearing All Employees from Database")
print("=" * 50)

from hr.models import Employee

try:
    # Get current count
    current_count = Employee.objects.count()
    print(f"📊 Current employee count: {current_count}")
    
    if current_count > 0:
        # Show some employees that will be deleted
        print("\n👥 Sample employees to be deleted:")
        for i, emp in enumerate(Employee.objects.all()[:3], 1):
            print(f"  {i}. {emp.emp_code}: {emp.first_name} {emp.last_name}")
        
        if current_count > 3:
            print(f"  ... and {current_count - 3} more")
        
        # Perform deletion
        print(f"\n🗑️ Deleting all {current_count} employees...")
        deleted_count, deletion_details = Employee.objects.all().delete()
        
        print(f"✅ Successfully deleted {deleted_count} employee records")
        
        # Verify deletion
        remaining_count = Employee.objects.count()
        print(f"📊 Remaining employees: {remaining_count}")
        
        if remaining_count == 0:
            print("\n🎉 SUCCESS: Employee table is now completely empty!")
            print("📝 You can now test creating new employees with a clean slate")
        else:
            print(f"\n⚠️ WARNING: {remaining_count} employees still remain")
            
    else:
        print("ℹ️ Employee table is already empty")
        
except Exception as e:
    print(f"❌ Error during deletion: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("🔄 Next steps:")
print("1. Start Django server: python manage.py runserver 8000")
print("2. Test employee list: http://localhost:8000/app/hr/employees (should show 0)")
print("3. Create new employee: http://localhost:8000/app/hr/employees/new")
print("4. Verify save functionality works end-to-end")
