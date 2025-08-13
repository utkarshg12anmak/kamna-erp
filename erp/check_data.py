from django.db import connection

cursor = connection.cursor()

# Check existing departments
cursor.execute("SELECT DISTINCT department FROM hr_employee WHERE department IS NOT NULL AND department != ''")
departments = [row[0] for row in cursor.fetchall()]
print('Existing departments:', departments)

# Check existing designations
cursor.execute("SELECT DISTINCT designation FROM hr_employee WHERE designation IS NOT NULL AND designation != ''")
designations = [row[0] for row in cursor.fetchall()]
print('Existing designations:', designations)

# Check employee count
cursor.execute("SELECT COUNT(*) FROM hr_employee")
employee_count = cursor.fetchone()[0]
print(f'Total employees: {employee_count}')

# Sample employee data
cursor.execute("SELECT id, first_name, last_name, department, designation FROM hr_employee LIMIT 5")
employees = cursor.fetchall()
print('\nSample employee data:')
for emp in employees:
    print(f'  ID: {emp[0]}, Name: {emp[1]} {emp[2]}, Dept: {emp[3]}, Designation: {emp[4]}')
