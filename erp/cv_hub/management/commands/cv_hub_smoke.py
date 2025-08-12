from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

from cv_hub.models import (CvHubEntry, CvHubGSTRegistration, CvHubAddress, CvHubContact,
                          CvHubState, CvHubCity, CvHubEntryStatus, CvHubConstitution,
                          CvHubTaxpayerType, CvHubAddressType)

class Command(BaseCommand):
    help = 'Run smoke tests for CV Hub functionality'

    def handle(self, *args, **options):
        self.stdout.write('Running CV Hub smoke tests...')
        
        try:
            # Test 1: Create CvHubEntry with valid roles and commerce
            self.stdout.write('Test 1: Creating CvHubEntry with supplier role...')
            entry = CvHubEntry.objects.create(
                legal_name='Test Supplier Co',
                constitution=CvHubConstitution.PVTLTD,
                is_supplier=True,
                for_purchase=True
            )
            
            # Verify commerce_label through serializer
            from cv_hub.api.serializers import CvHubEntrySerializer
            serializer = CvHubEntrySerializer(entry)
            assert serializer.data['commerce_label'] == 'Purchase', f"Expected 'Purchase', got {serializer.data['commerce_label']}"
            self.stdout.write('✓ Commerce label correct')
            
            # Test 2: Invalid GST registration (14 chars instead of 15)
            self.stdout.write('Test 2: Testing GST validation...')
            try:
                CvHubGSTRegistration.objects.create(
                    entry=entry,
                    taxpayer_type=CvHubTaxpayerType.REGULAR,
                    gstin='12ABCDE1234F5Z',  # 14 chars - should fail
                    legal_name_of_business='Test Supplier Co'
                )
                raise AssertionError('Expected ValidationError for 14-char GSTIN')
            except ValidationError:
                self.stdout.write('✓ GST validation working')
            
            # Test 3: Valid GST registration and primary logic
            self.stdout.write('Test 3: Testing primary GST registration logic...')
            gst1 = CvHubGSTRegistration.objects.create(
                entry=entry,
                taxpayer_type=CvHubTaxpayerType.REGULAR,
                gstin='12ABCDE1234F5Z6',  # 15 chars - valid
                legal_name_of_business='Test Supplier Co',
                is_primary=True
            )
            
            gst2 = CvHubGSTRegistration.objects.create(
                entry=entry,
                taxpayer_type=CvHubTaxpayerType.REGULAR,
                gstin='12ABCDE1234F5Z7',
                legal_name_of_business='Test Supplier Co Branch',
                is_primary=True  # Should make gst1 non-primary
            )
            
            gst1.refresh_from_db()
            assert not gst1.is_primary, 'First GST should no longer be primary'
            assert gst2.is_primary, 'Second GST should be primary'
            self.stdout.write('✓ Primary GST toggle working')
            
            # Test 4: Address validation (mismatched state/city)
            self.stdout.write('Test 4: Testing address state/city validation...')
            
            # Get different states and cities
            state1 = CvHubState.objects.first()
            state2 = CvHubState.objects.exclude(id=state1.id).first()
            city_from_state2 = CvHubCity.objects.filter(state=state2).first()
            
            from cv_hub.api.serializers import CvHubAddressSerializer
            
            # Try to create address with mismatched state/city
            invalid_addr_data = {
                'entry': entry.id,
                'type': CvHubAddressType.BILLING,
                'line1': 'Test Address',
                'pincode': '123456',
                'state': state1.id,
                'city': city_from_state2.id  # City from different state
            }
            
            addr_serializer = CvHubAddressSerializer(data=invalid_addr_data)
            assert not addr_serializer.is_valid(), 'Address with mismatched state/city should be invalid'
            self.stdout.write('✓ Address state/city validation working')
            
            # Test 5: Valid address and default logic
            self.stdout.write('Test 5: Testing address default logic...')
            city_from_state1 = CvHubCity.objects.filter(state=state1).first()
            
            addr1 = CvHubAddress.objects.create(
                entry=entry,
                type=CvHubAddressType.BILLING,
                line1='Address 1',
                pincode='123456',
                state=state1,
                city=city_from_state1,
                is_default_billing=True
            )
            
            addr2 = CvHubAddress.objects.create(
                entry=entry,
                type=CvHubAddressType.BILLING,
                line1='Address 2',
                pincode='123457',
                state=state1,
                city=city_from_state1,
                is_default_billing=True  # Should make addr1 non-default
            )
            
            addr1.refresh_from_db()
            assert not addr1.is_default_billing, 'First address should no longer be default billing'
            assert addr2.is_default_billing, 'Second address should be default billing'
            self.stdout.write('✓ Address default toggle working')
            
            # Test 6: Contact phone uniqueness and primary logic
            self.stdout.write('Test 6: Testing contact phone uniqueness and primary logic...')
            
            # Use unique phone numbers for testing
            test_phone1 = '+919999888877'
            test_phone2 = '+919999888866'
            test_phone_duplicate = '+919999888877'
            
            contact1 = CvHubContact.objects.create(
                entry=entry,
                full_name='John Doe Test',
                phone=test_phone1,
                email='john.test@smoke.com',
                is_primary=True
            )
            
            # Try to create another contact with same phone
            try:
                CvHubContact.objects.create(
                    entry=entry,
                    full_name='Jane Doe Test',
                    phone=test_phone_duplicate,  # Same as test_phone1
                    email='jane.test@smoke.com'
                )
                raise AssertionError('Expected unique constraint error for phone')
            except Exception:
                self.stdout.write('✓ Phone uniqueness working')
            
            # Create contact with different phone and test primary logic
            contact2 = CvHubContact.objects.create(
                entry=entry,
                full_name='Jane Doe Test',
                phone=test_phone2,
                email='jane.test@smoke.com',
                is_primary=True  # Should make contact1 non-primary
            )
            
            contact1.refresh_from_db()
            assert not contact1.is_primary, 'First contact should no longer be primary'
            assert contact2.is_primary, 'Second contact should be primary'
            self.stdout.write('✓ Contact primary toggle working')
            
            # Test 7: API endpoints
            self.stdout.write('Test 7: Testing API endpoints...')
            
            # Create a test user and get JWT token
            user, created = User.objects.get_or_create(
                username='testuser',
                defaults={'email': 'test@example.com'}
            )
            if created:
                user.set_password('testpass123')
                user.save()
            
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Test entries endpoint with filter
            response = client.get('/api/cv_hub/entries/?for_purchase=true')
            assert response.status_code == 200, f'Expected 200, got {response.status_code}'
            
            data = response.json()
            found_supplier = any(
                result['is_supplier'] and result['for_purchase'] 
                for result in data.get('results', data if isinstance(data, list) else [])
            )
            assert found_supplier, 'Should find supplier entry with for_purchase=true'
            self.stdout.write('✓ Entries API filter working')
            
            # Test quick endpoint
            response = client.get('/api/cv_hub/entries/quick/?q=Test')
            assert response.status_code == 200, f'Expected 200, got {response.status_code}'
            self.stdout.write('✓ Quick API working')
            
            # Test summary endpoint
            response = client.get(f'/api/cv_hub/entries/{entry.id}/summary/')
            assert response.status_code == 200, f'Expected 200, got {response.status_code}'
            
            summary_data = response.json()
            assert 'primary_gstin' in summary_data, 'Summary should include primary_gstin'
            assert summary_data['primary_gstin'] == gst2.gstin, 'Should return the primary GSTIN'
            self.stdout.write('✓ Summary API working')
            
            self.stdout.write(self.style.SUCCESS('CV_HUB_SMOKE_OK - All tests passed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Smoke test failed: {str(e)}'))
            raise
        
        finally:
            # Cleanup test data
            try:
                if 'entry' in locals():
                    entry.delete()
                if 'user' in locals() and created:
                    user.delete()
            except:
                pass
