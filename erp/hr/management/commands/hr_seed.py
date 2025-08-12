# HR Seed Data Management Command
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import date, timedelta
import random

from hr.models import (
    Employee, EmployeeDocument, OrgUnit, Position, 
    AccessProfile, EmploymentStatus, Gender, SalaryPeriod
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed HR module with sample data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--employees',
            type=int,
            default=50,
            help='Number of employees to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing HR data before seeding'
        )
        parser.add_argument(
            '--departments',
            nargs='+',
            default=['Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations'],
            help='Department names to use'
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing HR data...')
            self.clear_data()
        
        with transaction.atomic():
            self.stdout.write('Creating HR seed data...')
            
            # Create access profiles
            access_profiles = self.create_access_profiles()
            self.stdout.write(f'Created {len(access_profiles)} access profiles')
            
            # Create org units
            org_units = self.create_org_units(options['departments'])
            self.stdout.write(f'Created {len(org_units)} org units')
            
            # Create positions
            positions = self.create_positions()
            self.stdout.write(f'Created {len(positions)} positions')
            
            # Create employees
            employees = self.create_employees(
                count=options['employees'],
                departments=options['departments'],
                org_units=org_units,
                positions=positions,
                access_profiles=access_profiles
            )
            self.stdout.write(f'Created {len(employees)} employees')
            
            # Set up management hierarchy
            self.setup_management_hierarchy(employees)
            self.stdout.write('Set up management hierarchy')
            
            # Create sample documents
            documents = self.create_employee_documents(employees[:10])  # Only for first 10
            self.stdout.write(f'Created {len(documents)} sample documents')
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded HR module with {len(employees)} employees'
            )
        )
    
    def clear_data(self):
        """Clear existing HR data"""
        Employee.objects.all().delete()
        EmployeeDocument.objects.all().delete()
        OrgUnit.objects.all().delete()
        Position.objects.all().delete()
        AccessProfile.objects.all().delete()
    
    def create_access_profiles(self):
        """Create sample access profiles"""
        profiles_data = [
            {'name': 'Admin', 'description': 'Full system access'},
            {'name': 'Manager', 'description': 'Management level access'},
            {'name': 'Employee', 'description': 'Standard employee access'},
            {'name': 'Intern', 'description': 'Limited intern access'},
            {'name': 'Contractor', 'description': 'Contractor access'},
        ]
        
        profiles = []
        for data in profiles_data:
            profile, created = AccessProfile.objects.get_or_create(**data)
            profiles.append(profile)
        
        return profiles
    
    def create_org_units(self, departments):
        """Create organizational units"""
        # Create company root
        company, _ = OrgUnit.objects.get_or_create(
            name='Kamna Technologies',
            code='KT',
            type='Company'
        )
        
        org_units = [company]
        
        # Create department units
        for dept in departments:
            unit, _ = OrgUnit.objects.get_or_create(
                name=dept,
                code=dept[:3].upper(),
                parent=company,
                type='Department'
            )
            org_units.append(unit)
            
            # Create sub-units for larger departments
            if dept in ['Engineering', 'Sales']:
                sub_units = [
                    f'{dept} - Team A',
                    f'{dept} - Team B'
                ]
                for sub_unit in sub_units:
                    sub, _ = OrgUnit.objects.get_or_create(
                        name=sub_unit,
                        code=f'{dept[:2]}{sub_unit[-1]}',
                        parent=unit,
                        type='Team'
                    )
                    org_units.append(sub)
        
        return org_units
    
    def create_positions(self):
        """Create job positions"""
        positions_data = [
            # Engineering
            {'title': 'Software Engineer', 'grade': 'L2', 'family': 'Engineering'},
            {'title': 'Senior Software Engineer', 'grade': 'L3', 'family': 'Engineering'},
            {'title': 'Lead Software Engineer', 'grade': 'L4', 'family': 'Engineering'},
            {'title': 'Engineering Manager', 'grade': 'M1', 'family': 'Management'},
            {'title': 'DevOps Engineer', 'grade': 'L3', 'family': 'Engineering'},
            {'title': 'QA Engineer', 'grade': 'L2', 'family': 'Engineering'},
            
            # Sales
            {'title': 'Sales Executive', 'grade': 'S1', 'family': 'Sales'},
            {'title': 'Senior Sales Executive', 'grade': 'S2', 'family': 'Sales'},
            {'title': 'Sales Manager', 'grade': 'M1', 'family': 'Management'},
            {'title': 'Business Development', 'grade': 'S2', 'family': 'Sales'},
            
            # Marketing
            {'title': 'Marketing Executive', 'grade': 'M1', 'family': 'Marketing'},
            {'title': 'Digital Marketing Specialist', 'grade': 'M2', 'family': 'Marketing'},
            {'title': 'Marketing Manager', 'grade': 'M1', 'family': 'Management'},
            
            # Finance
            {'title': 'Accountant', 'grade': 'F1', 'family': 'Finance'},
            {'title': 'Senior Accountant', 'grade': 'F2', 'family': 'Finance'},
            {'title': 'Finance Manager', 'grade': 'M1', 'family': 'Management'},
            
            # HR
            {'title': 'HR Executive', 'grade': 'H1', 'family': 'HR'},
            {'title': 'HR Manager', 'grade': 'M1', 'family': 'Management'},
            {'title': 'Recruiter', 'grade': 'H1', 'family': 'HR'},
            
            # Operations
            {'title': 'Operations Executive', 'grade': 'O1', 'family': 'Operations'},
            {'title': 'Operations Manager', 'grade': 'M1', 'family': 'Management'},
            
            # Generic
            {'title': 'Intern', 'grade': 'I1', 'family': 'Intern'},
            {'title': 'Contractor', 'grade': 'C1', 'family': 'Contract'},
        ]
        
        positions = []
        for data in positions_data:
            position, created = Position.objects.get_or_create(**data)
            positions.append(position)
        
        return positions
    
    def create_employees(self, count, departments, org_units, positions, access_profiles):
        """Create sample employees"""
        
        # Sample names
        first_names = [
            'Rahul', 'Priya', 'Amit', 'Sneha', 'Vikram', 'Anjali', 'Rohit', 'Kavya',
            'Arjun', 'Meera', 'Karan', 'Pooja', 'Suresh', 'Divya', 'Rajesh', 'Nisha',
            'Akash', 'Shreya', 'Varun', 'Asha', 'Nikhil', 'Ravi', 'Sanjay', 'Deepika',
            'Arun', 'Sonal', 'Manish', 'Ritu', 'Gaurav', 'Preeti'
        ]
        
        last_names = [
            'Sharma', 'Patel', 'Singh', 'Kumar', 'Gupta', 'Jain', 'Agarwal', 'Mishra',
            'Verma', 'Srivastava', 'Yadav', 'Pandey', 'Chauhan', 'Joshi', 'Mehta',
            'Shah', 'Kapoor', 'Malhotra', 'Arora', 'Bansal'
        ]
        
        # Salary ranges by department
        salary_ranges = {
            'Engineering': (60000, 150000),
            'Sales': (40000, 120000),
            'Marketing': (45000, 100000),
            'Finance': (50000, 110000),
            'HR': (45000, 90000),
            'Operations': (40000, 80000),
        }
        
        employees = []
        base_date = date.today() - timedelta(days=365*3)  # 3 years ago
        
        for i in range(count):
            # Generate random employee data
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            department = random.choice(departments)
            
            # Find suitable position and org unit for department
            dept_positions = [p for p in positions if department.lower() in p.title.lower() or p.family == 'Generic']
            if not dept_positions:
                dept_positions = positions[:5]  # Fallback
            
            position = random.choice(dept_positions)
            
            dept_org_units = [ou for ou in org_units if department in ou.name]
            if not dept_org_units:
                dept_org_units = org_units[1:7]  # Skip company root
            
            org_unit = random.choice(dept_org_units)
            
            # Generate salary in department range
            min_sal, max_sal = salary_ranges.get(department, (40000, 80000))
            salary = random.randint(min_sal, max_sal)
            
            # Random joining date in last 3 years
            joining_days_ago = random.randint(30, 365*3)
            joining_date = date.today() - timedelta(days=joining_days_ago)
            
            # Birth date (22-60 years old)
            birth_years_ago = random.randint(22, 60) * 365
            birth_date = date.today() - timedelta(days=birth_years_ago)
            
            # Generate employee
            employee = Employee.objects.create(
                first_name=first_name,
                last_name=last_name,
                gender=random.choice([Gender.MALE, Gender.FEMALE, Gender.OTHER, Gender.NA]),
                email=f"{first_name.lower()}.{last_name.lower()}{i}@kamna.com",
                phone=f"+91 {random.randint(7000000000, 9999999999)}",
                birth_date=birth_date,
                department=department,
                designation=position.title,
                position=position,
                org_unit=org_unit,
                status=random.choice([
                    EmploymentStatus.ACTIVE, 
                    EmploymentStatus.ACTIVE,  # Weight towards active
                    EmploymentStatus.ACTIVE,
                    EmploymentStatus.ON_LEAVE,
                    EmploymentStatus.INACTIVE
                ]),
                date_of_joining=joining_date,
                salary_amount=salary,
                salary_currency='INR',
                salary_period=SalaryPeriod.MONTHLY,
                is_phone_assigned=random.choice([True, False]),
                is_laptop_assigned=random.choice([True, False]),
                access_profile=random.choice(access_profiles)
            )
            
            # Add phone/laptop details if assigned
            if employee.is_phone_assigned:
                employee.company_assigned_phone_number = f"+91 {random.randint(7000000000, 9999999999)}"
            
            if employee.is_laptop_assigned:
                laptop_models = ['Dell Latitude 5520', 'HP EliteBook 850', 'Lenovo ThinkPad X1', 'MacBook Pro 14"']
                employee.company_assigned_laptop = f"{random.choice(laptop_models)} - {random.randint(1000, 9999)}"
            
            employee.save()
            employees.append(employee)
        
        return employees
    
    def setup_management_hierarchy(self, employees):
        """Set up manager relationships"""
        # Get potential managers (senior positions)
        managers = [emp for emp in employees if 'Manager' in emp.designation or 'Lead' in emp.designation]
        
        # Assign managers to employees
        non_managers = [emp for emp in employees if emp not in managers]
        
        for employee in non_managers:
            # Find manager in same department
            dept_managers = [m for m in managers if m.department == employee.department]
            if dept_managers:
                employee.manager = random.choice(dept_managers)
                employee.save()
        
        # Set org unit managers
        for org_unit in OrgUnit.objects.filter(type__in=['Department', 'Team']):
            dept_managers = [m for m in managers if m.department in org_unit.name]
            if dept_managers:
                org_unit.manager = random.choice(dept_managers)
                org_unit.save()
    
    def create_employee_documents(self, employees):
        """Create sample documents for some employees"""
        doc_types = ['OFFER', 'APPOINT', 'OTHER']
        documents = []
        
        for employee in employees:
            # Create 1-3 documents per employee
            num_docs = random.randint(1, 3)
            
            for _ in range(num_docs):
                doc_type = random.choice(doc_types)
                
                # Generate document number
                if doc_type == 'OFFER':
                    number = f"OFFER-{employee.emp_code}-{random.randint(100, 999)}"
                elif doc_type == 'APPOINT':
                    number = f"APPOINT-{employee.emp_code}-{random.randint(100, 999)}"
                else:
                    number = f"DOC-{employee.emp_code}-{random.randint(100, 999)}"
                
                document = EmployeeDocument.objects.create(
                    employee=employee,
                    doc_type=doc_type,
                    number=number,
                    issued_on=employee.date_of_joining,
                    notes=f"Sample {doc_type.lower()} document for {employee.first_name}"
                )
                documents.append(document)
        
        return documents
