from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Employee, EmployeeDocument, AccessProfile
User = get_user_model()

class AccessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessProfile
        fields = ['id','name','description']

class EmployeeListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    aadhaar_masked = serializers.SerializerMethodField()
    class Meta:
        model = Employee
        fields = ['id','emp_code','full_name','email','phone','department','designation','date_of_joining','status','aadhaar_masked','pan_number','profile_image']
    def get_full_name(self,o):
        return (f"{o.first_name} {o.last_name}").strip()
    def get_aadhaar_masked(self,o):
        return f"****{o.aadhaar_last4}" if o.aadhaar_last4 else ''

class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)
    aadhaar_masked = serializers.SerializerMethodField(read_only=True)
    create_user = serializers.BooleanField(write_only=True, required=False, default=False)
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    is_staff = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Employee
        fields = ['id','emp_code','first_name','last_name','full_name','email','phone','birth_date','profile_image',
                  'aadhaar_last4','aadhaar_masked','aadhaar_doc_front','aadhaar_doc_back','pan_number','pan_doc',
                  'department','designation','manager','status','date_of_joining','salary_amount','salary_currency','salary_period',
                  'access_profile','user','created_at','updated_at','create_user','username','is_staff']
        read_only_fields = ['emp_code','created_at','updated_at','user']

    def get_full_name(self,o):
        return (f"{o.first_name} {o.last_name}").strip()
    def get_aadhaar_masked(self,o):
        return f"XXXX-XXXX-{o.aadhaar_last4}" if o.aadhaar_last4 else ''

    def validate(self, attrs):
        email = attrs.get('email') or getattr(self.instance,'email',None)
        phone = attrs.get('phone') or getattr(self.instance,'phone',None)
        if not email and not phone:
            raise serializers.ValidationError('Provide at least one of email or phone')
        bd = attrs.get('birth_date', getattr(self.instance,'birth_date', None))
        doj = attrs.get('date_of_joining', getattr(self.instance,'date_of_joining', None))
        if bd and doj and doj < bd:
            raise serializers.ValidationError('Date of joining cannot be before birth date')
        return attrs

    def create(self, validated):
        create_user = validated.pop('create_user', False)
        username = validated.pop('username', '') or validated.get('emp_code')
        is_staff = validated.pop('is_staff', False)
        emp = super().create(validated)
        if create_user and not emp.user:
            uname = username or emp.emp_code
            user = User.objects.create_user(username=uname, email=emp.email or '', password=User.objects.make_random_password())
            user.is_staff = bool(is_staff)
            user.save(update_fields=['is_staff'])
            emp.user = user
            emp.save(update_fields=['user'])
        return emp
