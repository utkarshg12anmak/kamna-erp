from django.contrib import admin
from .models import Employee, EmployeeDocument, AccessProfile, EmploymentStatus

@admin.action(description="Mark selected employees as EXITED")
def mark_exited(modeladmin, request, queryset):
    queryset.update(status=EmploymentStatus.EXITED)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("emp_code","first_name","department","designation","status","date_of_joining")
    search_fields = ("first_name","last_name","emp_code","email","phone")
    list_filter = ("status","department","designation")
    actions = [mark_exited]

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ("employee","doc_type","number","issued_on")
    search_fields = ("employee__emp_code","number")
    list_filter = ("doc_type",)

@admin.register(AccessProfile)
class AccessProfileAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
