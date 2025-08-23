from django.test import TestCase
from geo.models import State, City, Pincode, Territory, TerritoryMember, TerritoryCoverage
from geo.services import rebuild_territory_coverage

class TerritoryCoverageTestCase(TestCase):
    def setUp(self):
        # Create test geo data
        self.state_dl = State.objects.create(code='DL', name='Delhi')
        self.state_up = State.objects.create(code='UP', name='Uttar Pradesh')
        
        self.city_delhi = City.objects.create(state=self.state_dl, name='New Delhi')
        self.city_ghaziabad = City.objects.create(state=self.state_up, name='Ghaziabad')
        
        self.pin_110001 = Pincode.objects.create(state=self.state_dl, city=self.city_delhi, code='110001')
        self.pin_110002 = Pincode.objects.create(state=self.state_dl, city=self.city_delhi, code='110002')
        self.pin_201001 = Pincode.objects.create(state=self.state_up, city=self.city_ghaziabad, code='201001')
        self.pin_inactive = Pincode.objects.create(state=self.state_dl, city=self.city_delhi, code='110003', is_active=False)
        
        # Create territories
        self.territory_state = Territory.objects.create(code='T_STATE_DL', name='Delhi State Territory', type='STATE')
        self.territory_city = Territory.objects.create(code='T_CITY_DELHI', name='Delhi City Territory', type='CITY')
        self.territory_pincode = Territory.objects.create(code='T_PIN_110001', name='Pincode 110001 Territory', type='PINCODE')

    def test_state_member_builds_all_state_pincodes(self):
        """Test that adding a STATE member includes all active pincodes in that state"""
        TerritoryMember.objects.create(territory=self.territory_state, state=self.state_dl)
        
        coverage = TerritoryCoverage.objects.filter(territory=self.territory_state)
        covered_pincodes = set(coverage.values_list('pincode__code', flat=True))
        
        # Should include active pincodes from Delhi state
        expected_pincodes = {'110001', '110002'}  # Excluding inactive 110003
        self.assertEqual(covered_pincodes, expected_pincodes)

    def test_city_member_builds_its_pincodes(self):
        """Test that adding a CITY member includes all active pincodes in that city"""
        TerritoryMember.objects.create(territory=self.territory_city, city=self.city_delhi)
        
        coverage = TerritoryCoverage.objects.filter(territory=self.territory_city)
        covered_pincodes = set(coverage.values_list('pincode__code', flat=True))
        
        # Should include active pincodes from Delhi city only
        expected_pincodes = {'110001', '110002'}  # Excluding inactive 110003
        self.assertEqual(covered_pincodes, expected_pincodes)

    def test_pincode_member_adds_single(self):
        """Test that adding a PINCODE member includes only that single pincode"""
        TerritoryMember.objects.create(territory=self.territory_pincode, pincode=self.pin_110001)
        
        coverage = TerritoryCoverage.objects.filter(territory=self.territory_pincode)
        covered_pincodes = set(coverage.values_list('pincode__code', flat=True))
        
        # Should include only the specific pincode
        expected_pincodes = {'110001'}
        self.assertEqual(covered_pincodes, expected_pincodes)

    def test_removing_member_shrinks_coverage(self):
        """Test that removing a territory member reduces coverage"""
        # Add state member first
        member = TerritoryMember.objects.create(territory=self.territory_state, state=self.state_dl)
        
        initial_coverage = TerritoryCoverage.objects.filter(territory=self.territory_state).count()
        self.assertGreater(initial_coverage, 0)
        
        # Remove the member
        member.delete()
        
        final_coverage = TerritoryCoverage.objects.filter(territory=self.territory_state).count()
        self.assertEqual(final_coverage, 0)

    def test_inactive_pincode_excluded(self):
        """Test that inactive pincodes are excluded from coverage"""
        TerritoryMember.objects.create(territory=self.territory_state, state=self.state_dl)
        
        coverage = TerritoryCoverage.objects.filter(territory=self.territory_state)
        covered_pincodes = set(coverage.values_list('pincode__code', flat=True))
        
        # Should not include inactive pincode 110003
        self.assertNotIn('110003', covered_pincodes)
        self.assertIn('110001', covered_pincodes)
        self.assertIn('110002', covered_pincodes)
