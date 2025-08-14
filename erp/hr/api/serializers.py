from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Employee, EmployeeDocument, AccessProfile, OrgUnit, Position, HRFieldChange, EmploymentStatus
from ..utils import mask_value

User = get_user_model()

class AccessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessProfile
        fields = ['id', 'name', 'description']

class OrgUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgUnit
        fields = ['id', 'name', 'code', 'parent', 'type', 'manager', 'status']

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'title', 'grade', 'family']

class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = ['id', 'employee', 'doc_type', 'number', 'file', 'issued_on', 'valid_till', 'notes', 'created_at']

class HRFieldChangeSerializer(serializers.ModelSerializer):
    old_value_masked = serializers.SerializerMethodField()
    new_value_masked = serializers.SerializerMethodField()
    
    class Meta:
        model = HRFieldChange
        fields = ['id', 'field_name', 'old_value_masked', 'new_value_masked', 'changed_by', 'changed_at', 'source', 'ip_address']
    
    def get_old_value_masked(self, o):
        return o.old_value
    
    def get_new_value_masked(self, o):
        return o.new_value

class EmployeeListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    aadhaar_masked = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    user_username = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = ['id', 'emp_code', 'first_name', 'last_name', 'full_name', 'gender', 'email', 'phone', 'department', 'designation', 
                 'date_of_joining', 'status', 'aadhaar_masked', 'pan_number', 'profile_image', 
                 'is_phone_assigned', 'is_laptop_assigned', 'manager_name', 'user_username', 'user_id']
    
    def get_full_name(self, o):
        return f"{o.first_name} {o.last_name}".strip()
    
    def get_aadhaar_masked(self, o):
        return f"****{o.aadhaar_last4}" if o.aadhaar_last4 else ''
    
    def get_manager_name(self, o):
        if o.manager:
            return f"{o.manager.first_name} {o.manager.last_name}".strip()
        return None
    
    def get_user_username(self, o):
        return o.user.username if o.user else None
    
    def get_user_id(self, o):
        return o.user.id if o.user else None

class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)
    aadhaar_masked = serializers.SerializerMethodField(read_only=True)
    create_user = serializers.BooleanField(write_only=True, required=False, default=False)
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    is_staff = serializers.BooleanField(write_only=True, required=False, default=False)
    
    class Meta:
        model = Employee
        fields = ['id', 'emp_code', 'first_name', 'last_name', 'full_name', 'gender', 'email', 'phone', 'birth_date', 'profile_image',
                 'aadhaar_last4', 'aadhaar_masked', 'aadhaar_doc_front', 'aadhaar_doc_back', 'pan_number', 'pan_doc',
                 'department', 'designation', 'position', 'org_unit', 'manager', 'status', 'date_of_joining',
                 'salary_amount', 'salary_currency', 'salary_period', 'is_phone_assigned', 'company_assigned_phone_number', 
                 'is_laptop_assigned', 'company_assigned_laptop', 'access_profile', 'user', 'created_at', 'updated_at', 
                 'create_user', 'username', 'is_staff']
        read_only_fields = ['emp_code', 'created_at', 'updated_at', 'user']
    
    def get_full_name(self, o):
        return f"{o.first_name} {o.last_name}".strip()
    
    def get_aadhaar_masked(self, o):
        return f"XXXX-XXXX-{o.aadhaar_last4}" if o.aadhaar_last4 else ''
    
    def validate(self, attrs):
        email = attrs.get('email') or getattr(self.instance, 'email', None)
        phone = attrs.get('phone') or getattr(self.instance, 'phone', None)
        if not email and not phone:
            raise serializers.ValidationError('Provide at least one of email or phone')
        
        bd = attrs.get('birth_date', getattr(self.instance, 'birth_date', None))
        doj = attrs.get('date_of_joining', getattr(self.instance, 'date_of_joining', None))
        if bd and doj and doj < bd:
            raise serializers.ValidationError('Date of joining cannot be before birth date')
        
        if attrs.get('is_phone_assigned') and not attrs.get('company_assigned_phone_number') and not getattr(self.instance, 'company_assigned_phone_number', ''):
            raise serializers.ValidationError('Phone number required when phone is assigned')
        
        if attrs.get('is_laptop_assigned') and not attrs.get('company_assigned_laptop') and not getattr(self.instance, 'company_assigned_laptop', ''):
            raise serializers.ValidationError('Laptop tag/serial required when laptop is assigned')
        
        return attrs
    
    def create(self, validated):
        create_user = validated.pop('create_user', False)
        username = validated.pop('username', '') or validated.get('emp_code')
        is_staff = validated.pop('is_staff', False)
        
        emp = super().create(validated)
        
        if create_user and not emp.user:
            uname = username or emp.emp_code
            user = User.objects.create_user(
                username=uname, 
                email=emp.email or '', 
                password=User.objects.make_random_password()
            )
            user.is_staff = bool(is_staff)
            user.save(update_fields=['is_staff'])
            emp.user = user
            emp.save(update_fields=['user'])
        
        return emp

class AvailableUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
