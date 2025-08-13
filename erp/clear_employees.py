from hr.models import Employee

# Show current count
count_before = Employee.objects.count()
print(f"Employees before deletion: {count_before}")

# Delete all employees
if count_before > 0:
    deleted_count, _ = Employee.objects.all().delete()
    print(f"Successfully deleted {deleted_count} employees")
else:
    print("No employees to delete")

# Verify deletion
count_after = Employee.objects.count()
print(f"Employees after deletion: {count_after}")

if count_after == 0:
    print("✅ Employee table is now empty!")
else:
    print(f"⚠️ {count_after} employees still remain")
