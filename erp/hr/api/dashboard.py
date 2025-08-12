from datetime import date, timedelta
from calendar import monthrange
from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Employee, EmploymentStatus, SalaryPeriod

class HRDashboardSummary(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        today = date.today()
        m = today.month
        y = today.year
        
        total_active = Employee.objects.filter(status=EmploymentStatus.ACTIVE).count()
        birthdays = Employee.objects.filter(birth_date__month=m).count()
        anniversaries = Employee.objects.filter(date_of_joining__month=m).count()
        
        qs = Employee.objects.filter(status=EmploymentStatus.ACTIVE)
        
        # compute in Python for clarity
        total_monthly = 0
        for e in qs.only('salary_amount', 'salary_period'):
            total_monthly += float(e.salary_amount) if e.salary_period == SalaryPeriod.MONTHLY else float(e.salary_amount) / 12.0
        
        return Response({
            'total_active': total_active,
            'birthdays_this_month': birthdays,
            'anniversaries_this_month': anniversaries,
            'monthly_salary_run': round(total_monthly, 2)
        })

class HRDashboardUpcoming(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        typ = request.GET.get('type', 'birthday')
        days = int(request.GET.get('days', '14'))
        today = date.today()
        end = today + timedelta(days=days)
        
        def within(d):
            nd = d.replace(year=today.year)
            if today <= nd <= end:
                return True
            return False
        
        items = []
        for e in Employee.objects.filter(status=EmploymentStatus.ACTIVE).only('id', 'first_name', 'last_name', 'birth_date', 'date_of_joining', 'emp_code'):
            if typ == 'birthday' and e.birth_date and within(e.birth_date):
                items.append({
                    'id': e.id,
                    'name': f"{e.first_name} {e.last_name}", 
                    'date': e.birth_date.replace(year=today.year), 
                    'emp_code': e.emp_code
                })
            if typ == 'anniversary' and e.date_of_joining and within(e.date_of_joining):
                items.append({
                    'id': e.id,
                    'name': f"{e.first_name} {e.last_name}", 
                    'date': e.date_of_joining.replace(year=today.year), 
                    'years': max(0, today.year - e.date_of_joining.year), 
                    'emp_code': e.emp_code
                })
        
        return Response(sorted(items, key=lambda x: x['date']))
