from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt  
@require_http_methods(["GET", "POST", "DELETE"])
def employees_api(request):
    """Simple employee API endpoint that actually returns database data"""
    
    if request.method == "GET":
        try:
            # Import here to avoid circular imports
            from hr.models import Employee
            
            # Get all employees and convert to JSON-serializable format
            employees = []
            for emp in Employee.objects.all().order_by('emp_code'):
                employee_data = {
                    'id': emp.id,
                    'emp_code': emp.emp_code,
                    'first_name': emp.first_name,
                    'last_name': emp.last_name,
                    'email': emp.email,
                    'phone': emp.phone or '',
                    'department': emp.department or '',
                    'designation': emp.designation or '',
                    'status': emp.status,
                    'gender': emp.gender or '',
                    'date_of_joining': emp.date_of_joining.isoformat() if emp.date_of_joining else '',
                    'is_phone_assigned': emp.is_phone_assigned,
                    'is_laptop_assigned': emp.is_laptop_assigned,
                    'profile_image': emp.profile_image.url if emp.profile_image else None,
                    'manager_name': f"{emp.manager.first_name} {emp.manager.last_name}" if emp.manager else '',
                    'created_at': emp.created_at.isoformat() if emp.created_at else '',
                }
                employees.append(employee_data)
            
            return JsonResponse(employees, safe=False)
            
        except Exception as e:
            return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)
    
    elif request.method == "POST":
        # Actually create employee in database
        try:
            from hr.models import Employee
            from django.utils import timezone
            from datetime import datetime
            
            # Get form data
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            emp_code = request.POST.get('emp_code', '') or request.POST.get('employee_id', '')
            is_draft = request.POST.get('is_draft', 'false').lower() == 'true'
            
            # Basic validation
            if not first_name or not last_name or not email:
                return JsonResponse({
                    'error': 'First name, last name, and email are required'
                }, status=400)
            
            # Generate employee code if not provided
            if not emp_code:
                # Get the next employee number
                last_emp = Employee.objects.filter(emp_code__startswith='EMP-2025-').order_by('emp_code').last()
                if last_emp and last_emp.emp_code:
                    try:
                        last_num = int(last_emp.emp_code.split('-')[-1])
                        next_num = last_num + 1
                    except:
                        next_num = 1
                else:
                    next_num = 1
                emp_code = f"EMP-2025-{next_num:04d}"
            
            # Create the employee
            employee = Employee.objects.create(
                emp_code=emp_code,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=request.POST.get('phone', ''),
                department=request.POST.get('department', ''),
                designation=request.POST.get('designation', ''),
                gender=request.POST.get('gender', 'OTHER'),
                birth_date=None,  # Can be added later
                status='DRAFT' if is_draft else 'ACTIVE',
                date_of_joining=timezone.now().date(),
                salary_amount=0,
                salary_currency='USD',
                salary_period='MONTHLY',
                is_phone_assigned=False,
                is_laptop_assigned=False,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            # Return the created employee data
            employee_data = {
                'id': employee.id,
                'emp_code': employee.emp_code,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'email': employee.email,
                'phone': employee.phone or '',
                'department': employee.department or '',
                'designation': employee.designation or '',
                'status': employee.status,
                'gender': employee.gender or '',
                'date_of_joining': employee.date_of_joining.isoformat() if employee.date_of_joining else '',
                'is_phone_assigned': employee.is_phone_assigned,
                'is_laptop_assigned': employee.is_laptop_assigned,
                'profile_image': None,
                'manager_name': '',
                'created_at': employee.created_at.isoformat() if employee.created_at else '',
                'is_draft': is_draft
            }
            
            return JsonResponse(employee_data, status=201)
            
        except Exception as e:
            return JsonResponse({'error': f'Creation error: {str(e)}'}, status=400)
    
    elif request.method == "DELETE":
        # Delete all employees endpoint
        try:
            from hr.models import Employee
            
            current_count = Employee.objects.count()
            if current_count > 0:
                deleted_count, _ = Employee.objects.all().delete()
                return JsonResponse({
                    'message': f'Successfully deleted {deleted_count} employees',
                    'deleted_count': deleted_count,
                    'remaining_count': Employee.objects.count()
                }, status=200)
            else:
                return JsonResponse({
                    'message': 'No employees found to delete',
                    'deleted_count': 0,
                    'remaining_count': 0
                }, status=200)
                
        except Exception as e:
            return JsonResponse({'error': f'Delete error: {str(e)}'}, status=500)

@csrf_exempt  
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def employee_detail_api(request, employee_id):
    """API endpoint for individual employee operations"""
    
    try:
        from hr.models import Employee
        
        # Get employee by ID
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        if request.method == "GET":
            # Return individual employee data
            employee_data = {
                'id': employee.id,
                'emp_code': employee.emp_code,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'email': employee.email,
                'phone': employee.phone or '',
                'department': employee.department or '',
                'designation': employee.designation or '',
                'status': employee.status,
                'gender': employee.gender or '',
                'birth_date': employee.birth_date.isoformat() if employee.birth_date else '',
                'date_of_joining': employee.date_of_joining.isoformat() if employee.date_of_joining else '',
                'is_phone_assigned': employee.is_phone_assigned,
                'is_laptop_assigned': employee.is_laptop_assigned,
                'company_assigned_phone_number': employee.company_assigned_phone_number or '',
                'company_assigned_laptop': employee.company_assigned_laptop or '',
                'profile_image': employee.profile_image.url if employee.profile_image else None,
                'manager_name': f"{employee.manager.first_name} {employee.manager.last_name}" if employee.manager else '',
                'manager': employee.manager.id if employee.manager else None,
                'org_unit': employee.org_unit.id if employee.org_unit else None,
                'position': employee.position.id if employee.position else None,
                'access_profile': employee.access_profile.id if employee.access_profile else None,
                'salary_amount': str(employee.salary_amount),
                'salary_currency': employee.salary_currency,
                'salary_period': employee.salary_period,
                'aadhaar_last4': employee.aadhaar_last4 or '',
                'pan_number': employee.pan_number or '',
                'created_at': employee.created_at.isoformat() if employee.created_at else '',
                'updated_at': employee.updated_at.isoformat() if employee.updated_at else '',
            }
            
            return JsonResponse(employee_data)
            
        elif request.method in ["PUT", "PATCH"]:
            # Update employee (for edit functionality)
            try:
                # Parse JSON data for updates
                data = json.loads(request.body)
                
                # Update all available fields if provided
                if 'first_name' in data:
                    employee.first_name = data['first_name']
                if 'last_name' in data:
                    employee.last_name = data['last_name']
                if 'emp_code' in data and data['emp_code']:
                    employee.emp_code = data['emp_code']
                if 'email' in data:
                    employee.email = data['email']
                if 'phone' in data:
                    employee.phone = data['phone']
                if 'department' in data:
                    employee.department = data['department']
                if 'designation' in data:
                    employee.designation = data['designation']
                if 'status' in data:
                    employee.status = data['status']
                if 'gender' in data:
                    employee.gender = data['gender']
                
                # Handle date fields
                if 'birth_date' in data and data['birth_date']:
                    from datetime import datetime
                    try:
                        employee.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Skip invalid date formats
                
                if 'date_of_joining' in data and data['date_of_joining']:
                    from datetime import datetime
                    try:
                        employee.date_of_joining = datetime.strptime(data['date_of_joining'], '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Skip invalid date formats
                
                # Handle salary fields
                if 'salary_amount' in data and data['salary_amount']:
                    from decimal import Decimal, InvalidOperation
                    try:
                        employee.salary_amount = Decimal(str(data['salary_amount']))
                    except (InvalidOperation, ValueError):
                        pass  # Skip invalid salary amounts
                
                if 'salary_currency' in data:
                    employee.salary_currency = data['salary_currency']
                if 'salary_period' in data:
                    employee.salary_period = data['salary_period']
                
                # Handle ID document fields
                if 'aadhaar_last4' in data:
                    employee.aadhaar_last4 = data['aadhaar_last4']
                if 'pan_number' in data:
                    employee.pan_number = data['pan_number']
                
                # Handle asset fields
                if 'is_phone_assigned' in data:
                    employee.is_phone_assigned = data['is_phone_assigned'] in ['true', True, '1', 1]
                if 'company_assigned_phone_number' in data:
                    employee.company_assigned_phone_number = data['company_assigned_phone_number']
                if 'is_laptop_assigned' in data:
                    employee.is_laptop_assigned = data['is_laptop_assigned'] in ['true', True, '1', 1]
                if 'company_assigned_laptop' in data:
                    employee.company_assigned_laptop = data['company_assigned_laptop']
                
                # Handle foreign key relationships (if IDs are provided)
                if 'manager' in data and data['manager']:
                    try:
                        manager_employee = Employee.objects.get(id=int(data['manager']))
                        employee.manager = manager_employee
                    except (Employee.DoesNotExist, ValueError):
                        pass  # Skip invalid manager ID
                
                # Handle org_unit, position, access_profile if models exist
                # (These would need to be imported and handled based on your models)
                
                from django.utils import timezone
                employee.updated_at = timezone.now()
                employee.save()
                
                return JsonResponse({
                    'message': 'Employee updated successfully',
                    'updated_fields': list(data.keys())
                })
                
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Update error: {str(e)}'}, status=400)
                
        elif request.method == "DELETE":
            # Delete individual employee
            employee.delete()
            return JsonResponse({'message': 'Employee deleted successfully'})
            
    except Exception as e:
        return JsonResponse({'error': f'API error: {str(e)}'}, status=500)

# Import dashboard views
try:
    from .dashboard import HRDashboardSummary, HRDashboardUpcoming
    dashboard_views_imported = True
except ImportError as e:
    print(f"Warning: Could not import dashboard views: {e}")
    dashboard_views_imported = False

urlpatterns = [
    path('employees/', employees_api, name='employees-api'),
    path('employees/<int:employee_id>/', employee_detail_api, name='employee-detail-api'),
]

# Add dashboard endpoints if available
if dashboard_views_imported:
    urlpatterns += [
        path('dashboard/summary/', HRDashboardSummary.as_view(), name='hr-dashboard-summary'),
        path('dashboard/upcoming/', HRDashboardUpcoming.as_view(), name='hr-dashboard-upcoming'),
    ]
