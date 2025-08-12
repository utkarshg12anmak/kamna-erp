# HR Django Admin Configuration
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Employee, EmployeeDocument, OrgUnit, Position, 
    AccessProfile, HRFieldChange
)

@admin.register(Employee)
class EmployeeAdmin(SimpleHistoryAdmin):
    list_display = [
        'emp_code', 'get_full_name', 'email', 'phone', 
        'department', 'designation', 'status', 'get_manager',
        'date_of_joining', 'get_assets'
    ]
    list_filter = [
        'status', 'department', 'designation', 'gender',
        'is_phone_assigned', 'is_laptop_assigned', 'date_of_joining'
    ]
    search_fields = [
        'emp_code', 'first_name', 'last_name', 'email', 
        'phone', 'department', 'designation'
    ]
    ordering = ['emp_code', 'first_name']
    date_hierarchy = 'date_of_joining'
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('first_name', 'last_name'),
                ('emp_code', 'gender'),
                ('email', 'phone'),
                ('birth_date', 'profile_image')
            )
        }),
        ('Identity Documents', {
            'fields': (
                ('aadhaar_last4', 'pan_number'),
                ('aadhaar_doc_front', 'aadhaar_doc_back'),
                ('pan_doc',)
            ),
            'classes': ('collapse',)
        }),
        ('Job Details', {
            'fields': (
                ('department', 'designation'),
                ('position', 'org_unit'),
                ('manager', 'status'),
                ('date_of_joining', 'access_profile'),
                ('user',)
            )
        }),
        ('Payroll', {
            'fields': (
                ('salary_amount', 'salary_currency', 'salary_period'),
            ),
            'classes': ('collapse',)
        }),
        ('Company Assets', {
            'fields': (
                ('is_phone_assigned', 'company_assigned_phone_number'),
                ('is_laptop_assigned', 'company_assigned_laptop')
            ),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': (
                ('created_by', 'updated_by'),
                ('created_at', 'updated_at')
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'
    
    def get_manager(self, obj):
        if obj.manager:
            url = reverse('admin:hr_employee_change', args=[obj.manager.id])
            return format_html('<a href="{}">{}</a>', url, obj.manager)
        return '-'
    get_manager.short_description = 'Manager'
    
    def get_assets(self, obj):
        assets = []
        if obj.is_phone_assigned:
            assets.append('📱')
        if obj.is_laptop_assigned:
            assets.append('💻')
        return ''.join(assets) if assets else '-'
    get_assets.short_description = 'Assets'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(SimpleHistoryAdmin):
    list_display = [
        'employee', 'doc_type', 'number', 'issued_on', 
        'valid_till', 'created_at'
    ]
    list_filter = ['doc_type', 'issued_on', 'valid_till', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'number']
    date_hierarchy = 'created_at'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "employee":
            kwargs["queryset"] = Employee.objects.select_related().order_by('emp_code')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(OrgUnit)
class OrgUnitAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'code', 'type', 'get_parent', 'get_manager', 'status']
    list_filter = ['type', 'status']
    search_fields = ['name', 'code']
    ordering = ['name']
    
    def get_parent(self, obj):
        if obj.parent:
            url = reverse('admin:hr_orgunit_change', args=[obj.parent.id])
            return format_html('<a href="{}">{}</a>', url, obj.parent.name)
        return '-'
    get_parent.short_description = 'Parent Unit'
    
    def get_manager(self, obj):
        if obj.manager:
            url = reverse('admin:hr_employee_change', args=[obj.manager.id])
            return format_html('<a href="{}">{}</a>', url, obj.manager)
        return '-'
    get_manager.short_description = 'Manager'

@admin.register(Position)
class PositionAdmin(SimpleHistoryAdmin):
    list_display = ['title', 'grade', 'family']
    list_filter = ['grade', 'family']
    search_fields = ['title', 'grade', 'family']
    ordering = ['title']

@admin.register(AccessProfile)
class AccessProfileAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']
    ordering = ['name']

@admin.register(HRFieldChange)
class HRFieldChangeAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'field_name', 'old_value_short', 'new_value_short',
        'changed_by', 'changed_at', 'source', 'ip_address'
    ]
    list_filter = [
        'field_name', 'source', 'changed_at', 'changed_by'
    ]
    search_fields = [
        'employee__first_name', 'employee__last_name', 
        'employee__emp_code', 'field_name'
    ]
    date_hierarchy = 'changed_at'
    readonly_fields = [
        'employee', 'field_name', 'old_value', 'new_value',
        'changed_by', 'changed_at', 'source', 'request_id', 'ip_address'
    ]
    
    def has_add_permission(self, request):
        return False  # Field changes are created programmatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Field changes are immutable
    
    def old_value_short(self, obj):
        return self._truncate_value(obj.old_value)
    old_value_short.short_description = 'Old Value'
    
    def new_value_short(self, obj):
        return self._truncate_value(obj.new_value)
    new_value_short.short_description = 'New Value'
    
    def _truncate_value(self, value):
        if not value:
            return '-'
        return value[:50] + '...' if len(value) > 50 else value
