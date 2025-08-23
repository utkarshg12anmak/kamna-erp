"""
Tests for Territory admin-only functionality.

Test coverage:
- Territory type enforcement
- Member validation rules
- Type immutability after members exist
- CSV import functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from geo.models import State, City, Pincode, Territory, TerritoryMember

User = get_user_model()


class TerritoryModelTests(TestCase):
    """Test Territory model behaviors and validation."""
    
    def setUp(self):
        """Create test user and geo data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test geo data
        self.state = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.city = City.objects.create(
            state=self.state,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.pincode = Pincode.objects.create(
            state=self.state,
            city=self.city,
            code='282001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create inactive entities for testing
        self.inactive_state = State.objects.create(
            code='DL',
            name='Delhi',
            is_active=False,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_territory_normalization(self):
        """Test Territory code normalization (uppercase, strip whitespace)."""
        territory = Territory.objects.create(
            code='  test_code  ',
            name='  Test Territory  ',
            type='STATE',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(territory.code, 'TEST_CODE')
        self.assertEqual(territory.name, 'Test Territory')
    
    def test_territory_effective_date_validation(self):
        """Test Territory effective date validation."""
        with self.assertRaises(ValidationError):
            territory = Territory(
                code='TEST',
                name='Test Territory',
                type='STATE',
                effective_from='2025-12-31',
                effective_till='2025-01-01',  # Before effective_from
                created_by=self.user,
                updated_by=self.user
            )
            territory.clean()


class TerritoryMemberTests(TestCase):
    """Test TerritoryMember model behaviors and validation."""
    
    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create geo data
        self.state = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.city = City.objects.create(
            state=self.state,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.pincode = Pincode.objects.create(
            state=self.state,
            city=self.city,
            code='282001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create inactive entities
        self.inactive_city = City.objects.create(
            state=self.state,
            name='Inactive City',
            is_active=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create territories of different types
        self.state_territory = Territory.objects.create(
            code='STATE_TERR',
            name='State Territory',
            type='STATE',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.city_territory = Territory.objects.create(
            code='CITY_TERR',
            name='City Territory',
            type='CITY',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.pincode_territory = Territory.objects.create(
            code='PIN_TERR',
            name='Pincode Territory',
            type='PINCODE',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_city_territory_add_city_member_success(self):
        """Test adding a city member to CITY territory - should work."""
        member = TerritoryMember.objects.create(
            territory=self.city_territory,
            city=self.city
        )
        
        self.assertEqual(member.territory, self.city_territory)
        self.assertEqual(member.city, self.city)
        self.assertIsNone(member.state)
        self.assertIsNone(member.pincode)
    
    def test_city_territory_add_pincode_member_fails(self):
        """Test adding a pincode member to CITY territory - should fail."""
        with self.assertRaises(ValidationError):
            member = TerritoryMember(
                territory=self.city_territory,
                pincode=self.pincode
            )
            member.clean()
    
    def test_state_territory_requires_state(self):
        """Test STATE territory requires state member."""
        with self.assertRaises(ValidationError):
            member = TerritoryMember(
                territory=self.state_territory,
                city=self.city  # Wrong type
            )
            member.clean()
    
    def test_pincode_territory_requires_pincode(self):
        """Test PINCODE territory requires pincode member."""
        with self.assertRaises(ValidationError):
            member = TerritoryMember(
                territory=self.pincode_territory,
                state=self.state  # Wrong type
            )
            member.clean()
    
    def test_multiple_fields_not_allowed(self):
        """Test that exactly one field must be filled."""
        with self.assertRaises(ValidationError):
            member = TerritoryMember(
                territory=self.state_territory,
                state=self.state,
                city=self.city  # Multiple fields
            )
            member.clean()
    
    def test_no_fields_not_allowed(self):
        """Test that at least one field must be filled."""
        with self.assertRaises(ValidationError):
            member = TerritoryMember(
                territory=self.state_territory
                # No state/city/pincode
            )
            member.clean()
    
    def test_inactive_member_blocked(self):
        """Test that inactive geo entities cannot be added as members."""
        with self.assertRaises(ValidationError):
            member = TerritoryMember(
                territory=self.city_territory,
                city=self.inactive_city
            )
            member.clean()
    
    def test_unique_member_per_territory(self):
        """Test that same geo entity cannot be added twice to same territory."""
        # Add city member
        TerritoryMember.objects.create(
            territory=self.city_territory,
            city=self.city
        )
        
        # Try to add same city again
        with self.assertRaises(IntegrityError):
            TerritoryMember.objects.create(
                territory=self.city_territory,
                city=self.city
            )


class TerritoryTypeImmutabilityTests(TestCase):
    """Test Territory type immutability after members exist."""
    
    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.state = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.city = City.objects.create(
            state=self.state,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.territory = Territory.objects.create(
            code='TEST_TERR',
            name='Test Territory',
            type='CITY',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_type_change_allowed_when_no_members(self):
        """Test that type can be changed when no members exist."""
        # Should work since no members
        self.territory.type = 'STATE'
        self.territory.save()  # Should not raise error
        
        self.assertEqual(self.territory.type, 'STATE')
    
    def test_type_change_blocked_when_members_exist(self):
        """Test that type cannot be changed after members are added."""
        # Add a member
        TerritoryMember.objects.create(
            territory=self.territory,
            city=self.city
        )
        
        # Try to change type
        with self.assertRaises(ValidationError):
            self.territory.type = 'STATE'
            self.territory.save()


class TerritoryCSVImportTests(TestCase):
    """Test CSV import functionality (simulation)."""
    
    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create active geo data
        self.state1 = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.state2 = State.objects.create(
            code='MP',
            name='Madhya Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create inactive state
        self.inactive_state = State.objects.create(
            code='DL',
            name='Delhi',
            is_active=False,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create pincode territory
        self.pincode_territory = Territory.objects.create(
            code='PIN_TERR',
            name='Pincode Territory',
            type='PINCODE',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create pincodes
        self.city = City.objects.create(
            state=self.state1,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.pincode1 = Pincode.objects.create(
            state=self.state1,
            city=self.city,
            code='282001',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.pincode2 = Pincode.objects.create(
            state=self.state1,
            city=self.city,
            code='282002',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create inactive pincode
        self.inactive_pincode = Pincode.objects.create(
            state=self.state1,
            city=self.city,
            code='999999',
            is_active=False,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_csv_import_simulation_pincode_type(self):
        """Simulate CSV import for PINCODE type territory."""
        # Simulate adding valid pincodes
        from geo.models import TerritoryMember
        
        # Test data like CSV would provide
        csv_data = [
            {'PINCODE': '282001'},  # Valid active pincode
            {'PINCODE': '282002'},  # Valid active pincode
            {'PINCODE': '999999'},  # Inactive pincode (should be skipped)
            {'PINCODE': '000000'},  # Unknown pincode (should be skipped)
            {'PINCODE': '282001'},  # Duplicate (should be skipped)
        ]
        
        added = dupes = inactive = unknown = 0
        
        for row in csv_data:
            pc = (row['PINCODE'] or '').strip()
            p = Pincode.objects.filter(code=pc).first()
            
            if not p:
                unknown += 1
                continue
            if not p.is_active:
                inactive += 1
                continue
            
            obj, created = TerritoryMember.objects.get_or_create(
                territory=self.pincode_territory, 
                pincode=p
            )
            if created:
                added += 1
            else:
                dupes += 1
        
        # Verify results
        self.assertEqual(added, 2)  # 282001, 282002
        self.assertEqual(dupes, 1)  # 282001 duplicate
        self.assertEqual(inactive, 1)  # 999999
        self.assertEqual(unknown, 1)  # 000000
        
        # Verify members were actually added
        self.assertEqual(self.pincode_territory.members.count(), 2)
        self.assertTrue(
            TerritoryMember.objects.filter(
                territory=self.pincode_territory, 
                pincode=self.pincode1
            ).exists()
        )
        self.assertTrue(
            TerritoryMember.objects.filter(
                territory=self.pincode_territory, 
                pincode=self.pincode2
            ).exists()
        )
