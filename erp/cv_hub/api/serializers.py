from rest_framework import serializers
from ..models import (CvHubEntry, CvHubGSTRegistration, CvHubAddress, CvHubContact,
                      CvHubState, CvHubCity)

class CvHubStateSerializer(serializers.ModelSerializer):
    class Meta: model=CvHubState; fields=['id','name','code']
class CvHubCitySerializer(serializers.ModelSerializer):
    class Meta: model=CvHubCity; fields=['id','name','state']

class CvHubContactSerializer(serializers.ModelSerializer):
    class Meta: model=CvHubContact; fields=['id','entry','full_name','designation','phone','email','is_primary']

class CvHubAddressSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    city_name  = serializers.CharField(source='city.name', read_only=True)
    class Meta: model=CvHubAddress; fields=['id','entry','type','line1','line2','pincode','state','city','state_name','city_name','latitude','longitude','is_default_billing','is_default_shipping']
    def validate(self, attrs):
        st = attrs.get('state') or getattr(self.instance,'state',None)
        ct = attrs.get('city') or getattr(self.instance,'city',None)
        if st and ct and ct.state_id != st.id:
            raise serializers.ValidationError('City must belong to the selected State')
        return attrs

class CvHubGSTRegistrationSerializer(serializers.ModelSerializer):
    class Meta: model=CvHubGSTRegistration; fields=['id','entry','taxpayer_type','gstin','legal_name_of_business','trade_name','effective_date_of_registration','constitution_of_business','gstin_status','principal_place_of_business','business_activities','is_primary','status']

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
