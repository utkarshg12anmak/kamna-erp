from rest_framework import serializers
from ..models import (CvHubEntry, CvHubGSTRegistration, CvHubAddress, CvHubContact,
                      CvHubState, CvHubCity)

class CvHubStateSerializer(serializers.ModelSerializer):
    class Meta: 
        model = CvHubState
        fields = ['id','name','code']

class CvHubCitySerializer(serializers.ModelSerializer):
    class Meta: 
        model = CvHubCity
        fields = ['id','name','state']

class CvHubContactSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta: 
        model = CvHubContact
        fields = ['id','entry','first_name','last_name','full_name','designation','phone','email','is_primary','created_by_username','updated_by_username']

class CvHubAddressSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name  = serializers.CharField(source='city.name', read_only=True)
    
    class Meta: 
        model = CvHubAddress
        fields = ['id','entry','type','line1','line2','pincode','state','city','state_name','city_name','latitude','longitude','is_default_billing','is_default_shipping']
    
    def validate(self, attrs):
        st = attrs.get('state') or getattr(self.instance,'state',None)
        ct = attrs.get('city') or getattr(self.instance,'city',None)
        if st and ct and ct.state_id != st.id:
            raise serializers.ValidationError('City must belong to the selected State')
        return attrs

class CvHubGSTRegistrationSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta: 
        model = CvHubGSTRegistration
        fields = ['id','entry','taxpayer_type','gstin','legal_name_of_business','trade_name','effective_date_of_registration','constitution_of_business','gstin_status','principal_place_of_business','business_activities','is_primary','status','created_by_username','updated_by_username']
    
    def validate(self, attrs):
        gstin = attrs.get('gstin')
        taxpayer_type = attrs.get('taxpayer_type')
        
        # Skip validation for unregistered taxpayers
        if taxpayer_type == 'UNREGISTERED':
            return attrs
        
        # Check for duplicate GSTIN with meaningful error message
        if gstin:
            gstin = gstin.strip().upper()
            attrs['gstin'] = gstin  # Normalize the GSTIN
            
            # Check if GSTIN already exists (excluding current instance for updates)
            existing_gst = CvHubGSTRegistration.objects.filter(gstin=gstin)
            if self.instance:
                existing_gst = existing_gst.exclude(pk=self.instance.pk)
            
            if existing_gst.exists():
                existing_entry = existing_gst.first().entry
                raise serializers.ValidationError({
                    'gstin': f'GSTIN {gstin} is already registered to {existing_entry.legal_name}'
                })
        
        return attrs
    
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except Exception as e:
            # If we get a database integrity error, try to provide a meaningful message
            if 'unique_gstin_when_not_null' in str(e) or 'gstin' in str(e).lower():
                gstin = validated_data.get('gstin')
                if gstin:
                    existing_gst = CvHubGSTRegistration.objects.filter(gstin=gstin).first()
                    if existing_gst:
                        raise serializers.ValidationError({
                            'gstin': f'GSTIN {gstin} is already registered to {existing_gst.entry.legal_name}'
                        })
            raise serializers.ValidationError({'gstin': 'GSTIN already exists in the system'})
    
    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except Exception as e:
            # If we get a database integrity error, try to provide a meaningful message
            if 'unique_gstin_when_not_null' in str(e) or 'gstin' in str(e).lower():
                gstin = validated_data.get('gstin')
                if gstin:
                    existing_gst = CvHubGSTRegistration.objects.filter(gstin=gstin).exclude(pk=instance.pk).first()
                    if existing_gst:
                        raise serializers.ValidationError({
                            'gstin': f'GSTIN {gstin} is already registered to {existing_gst.entry.legal_name}'
                        })
            raise serializers.ValidationError({'gstin': 'GSTIN already exists in the system'})

class CvHubEntrySerializer(serializers.ModelSerializer):
    commerce_label = serializers.SerializerMethodField(read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = CvHubEntry
        fields = ['id','legal_name','trade_name','constitution','status','is_customer','is_supplier','is_vendor','is_logistics','for_sales','for_purchase','website','tags','created_at','updated_at','commerce_label','created_by_username','updated_by_username']
    
    def get_commerce_label(self,obj):
        return 'Both' if (obj.for_sales and obj.for_purchase) else ('Sales' if obj.for_sales else ('Purchase' if obj.for_purchase else '—'))

class CvHubEntryDetailSerializer(serializers.ModelSerializer):
    registrations = CvHubGSTRegistrationSerializer(many=True, read_only=True)
    addresses = CvHubAddressSerializer(many=True, read_only=True)
    contacts = CvHubContactSerializer(many=True, read_only=True)
    commerce_label = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = CvHubEntry
        fields = ['id','legal_name','trade_name','constitution','status','is_customer','is_supplier','is_vendor','is_logistics','for_sales','for_purchase','website','tags','commerce_label','registrations','addresses','contacts','created_at','updated_at','created_by_username','updated_by_username']
    
    def get_commerce_label(self,obj):
        return 'Both' if (obj.for_sales and obj.for_purchase) else ('Sales' if obj.for_sales else ('Purchase' if obj.for_purchase else '—'))
    
    class Meta: 
        model = CvHubGSTRegistration
        fields = ['id','entry','taxpayer_type','gstin','legal_name_of_business','trade_name','effective_date_of_registration','constitution_of_business','gstin_status','principal_place_of_business','business_activities','is_primary','status','created_by_username','updated_by_username']

class CvHubEntrySerializer(serializers.ModelSerializer):
    commerce_label = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = CvHubEntry
        fields = ['id','legal_name','trade_name','constitution','status','is_customer','is_supplier','is_vendor','is_logistics','for_sales','for_purchase','website','tags','created_at','updated_at','commerce_label']
    def get_commerce_label(self,obj):
        return 'Both' if (obj.for_sales and obj.for_purchase) else ('Sales' if obj.for_sales else ('Purchase' if obj.for_purchase else '—'))

class CvHubEntryDetailSerializer(serializers.ModelSerializer):
    registrations = CvHubGSTRegistrationSerializer(many=True, read_only=True)
    addresses = CvHubAddressSerializer(many=True, read_only=True)
    contacts = CvHubContactSerializer(many=True, read_only=True)
    commerce_label = serializers.SerializerMethodField()
    class Meta:
        model = CvHubEntry
        fields = ['id','legal_name','trade_name','constitution','status','is_customer','is_supplier','is_vendor','is_logistics','for_sales','for_purchase','website','tags','commerce_label','registrations','addresses','contacts','created_at','updated_at']
    def get_commerce_label(self,obj):
        return 'Both' if (obj.for_sales and obj.for_purchase) else ('Sales' if obj.for_sales else ('Purchase' if obj.for_purchase else '—'))
