from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["GET", "POST"])
def employees_api(request):
    """Simple employee API endpoint for testing"""
    if request.method == "GET":
        # Return empty list for now
        return JsonResponse([], safe=False)
    
    elif request.method == "POST":
        # For testing, just return success
        try:
            # Get form data
            data = {
                'id': 1,
                'first_name': request.POST.get('first_name', ''),
                'last_name': request.POST.get('last_name', ''),
                'email': request.POST.get('email', ''),
                'employee_id': request.POST.get('employee_id', ''),
                'is_draft': request.POST.get('is_draft', False)
            }
            return JsonResponse(data, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

urlpatterns = [
    path('employees/', employees_api, name='employees-api'),
]
