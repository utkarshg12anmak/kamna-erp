from django.core.management.base import BaseCommand
from django.db import transaction
from cv_hub.models import (CvHubState, CvHubCity, CvHubEntry, CvHubGSTRegistration, 
                          CvHubAddress, CvHubContact, CvHubEntryStatus, CvHubConstitution,
                          CvHubTaxpayerType, CvHubAddressType)
from datetime import date

class Command(BaseCommand):
    help = 'Seed CV Hub with initial states, cities, and demo entries'

    def handle(self, *args, **options):
        self.stdout.write('Seeding CV Hub data...')
        
        with transaction.atomic():
            # Create states
            states_data = [
                ('Uttar Pradesh', 'UP'),
                ('Delhi', 'DL'),
                ('Maharashtra', 'MH'),
                ('Karnataka', 'KA'),
                ('Tamil Nadu', 'TN'),
            ]
            
            for name, code in states_data:
                state, created = CvHubState.objects.get_or_create(
                    code=code,
                    defaults={'name': name}
                )
                if created:
                    self.stdout.write(f'Created state: {name} ({code})')
            
            # Create cities
            cities_data = [
                ('UP', ['Meerut', 'Lucknow', 'Noida', 'Ghaziabad']),
                ('DL', ['New Delhi', 'Delhi']),
                ('MH', ['Mumbai', 'Pune', 'Nagpur']),
                ('KA', ['Bengaluru', 'Mysuru']),
                ('TN', ['Chennai', 'Coimbatore']),
            ]
            
            for state_code, city_names in cities_data:
                state = CvHubState.objects.get(code=state_code)
                for city_name in city_names:
                    city, created = CvHubCity.objects.get_or_create(
                        state=state,
                        name=city_name
                    )
                    if created:
                        self.stdout.write(f'Created city: {city_name}, {state_code}')
            
            # Create demo entries
            
            # 1. B2C Unregistered Entry
            if not CvHubEntry.objects.filter(legal_name='Walk-in Customer').exists():
                b2c_entry = CvHubEntry.objects.create(
                    legal_name='Walk-in Customer',
                    trade_name='B2C Customer',
                    constitution=CvHubConstitution.INDIVIDUAL,
                    status=CvHubEntryStatus.ACTIVE,
                    is_customer=True,
                    for_sales=True
                )
                
                # Add unregistered GST registration
                CvHubGSTRegistration.objects.create(
                    entry=b2c_entry,
                    taxpayer_type=CvHubTaxpayerType.UNREGISTERED,
                    legal_name_of_business='Walk-in Customer',
                    is_primary=True
                )
                
                self.stdout.write('Created B2C unregistered entry')
            
            # 2. Registered Supplier Entry
            if not CvHubEntry.objects.filter(legal_name='ABC Supplies Pvt Ltd').exists():
                supplier_entry = CvHubEntry.objects.create(
                    legal_name='ABC Supplies Pvt Ltd',
                    trade_name='ABC Supplies',
                    constitution=CvHubConstitution.PVTLTD,
                    status=CvHubEntryStatus.ACTIVE,
                    is_supplier=True,
                    for_purchase=True,
                    website='https://abcsupplies.com'
                )
                
                # Add primary GST registration
                CvHubGSTRegistration.objects.create(
                    entry=supplier_entry,
                    taxpayer_type=CvHubTaxpayerType.REGULAR,
                    gstin='09ABCDE1234F5Z6',
                    legal_name_of_business='ABC Supplies Private Limited',
                    trade_name='ABC Supplies',
                    effective_date_of_registration=date(2020, 4, 1),
                    constitution_of_business=CvHubConstitution.PVTLTD,
                    principal_place_of_business='Industrial Area, Ghaziabad',
                    business_activities='Manufacturing and trading of industrial supplies',
                    is_primary=True
                )
                
                # Add billing address
                up_state = CvHubState.objects.get(code='UP')
                ghaziabad_city = CvHubCity.objects.get(state=up_state, name='Ghaziabad')
                
                CvHubAddress.objects.create(
                    entry=supplier_entry,
                    type=CvHubAddressType.BILLING,
                    line1='Plot 123, Industrial Area',
                    line2='Sector 5',
                    pincode='201009',
                    state=up_state,
                    city=ghaziabad_city,
                    is_default_billing=True
                )
                
                # Add shipping address (same as billing)
                CvHubAddress.objects.create(
                    entry=supplier_entry,
                    type=CvHubAddressType.SHIPPING,
                    line1='Plot 123, Industrial Area',
                    line2='Sector 5',
                    pincode='201009',
                    state=up_state,
                    city=ghaziabad_city,
                    is_default_shipping=True
                )
                
                # Add primary contact
                CvHubContact.objects.create(
                    entry=supplier_entry,
                    full_name='Rajesh Kumar',
                    designation='Sales Manager',
                    phone='+919876543210',
                    email='rajesh@abcsupplies.com',
                    is_primary=True
                )
                
                self.stdout.write('Created registered supplier entry with GST, address, and contact')
        
        self.stdout.write(self.style.SUCCESS('CV Hub seeding completed successfully!'))
