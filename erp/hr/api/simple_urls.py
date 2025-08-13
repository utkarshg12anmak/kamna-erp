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
        # For testing, just return success
        try:
            # Get form data
            data = {
                'id': 1,
                'first_name': request.POST.get('first_name', ''),
                'last_name': request.POST.get('last_name', ''),
                'email': request.POST.get('email', ''),
                'emp_code': request.POST.get('employee_id', ''),
                'is_draft': request.POST.get('is_draft', False)
            }
            return JsonResponse(data, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
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

urlpatterns = [
    path('employees/', employees_api, name='employees-api'),
]
