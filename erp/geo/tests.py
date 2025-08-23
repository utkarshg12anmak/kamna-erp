"""
Tests for geo app models, signals, and behaviors.

Test coverage:
- Model validation and normalization
- Cascade deactivation signals
- Unique constraints
- Data integrity
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from geo.models import State, City, Pincode

User = get_user_model()


class GeoModelTests(TestCase):
    """Test geo model behaviors and validation."""
    
    def setUp(self):
        """Create test user for audit trail."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_state_normalization(self):
        """Test State code normalization (uppercase, strip whitespace)."""
        state = State.objects.create(
            code='  up  ',  # Should be normalized to 'UP'
            name='  Uttar Pradesh  ',  # Should be stripped
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(state.code, 'UP')
        self.assertEqual(state.name, 'Uttar Pradesh')
    
    def test_state_unique_code(self):
        """Test State code uniqueness constraint."""
        State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should raise IntegrityError for duplicate code
        with self.assertRaises(IntegrityError):
            State.objects.create(
                code='UP',
                name='Different Name',
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_city_normalization(self):
        """Test City name normalization (strip whitespace)."""
        state = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        city = City.objects.create(
            state=state,
            name='  Agra  ',  # Should be stripped
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(city.name, 'Agra')
    
    def test_pincode_validation(self):
        """Test Pincode validation (6-digit format)."""
        state = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        city = City.objects.create(
            state=state,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Valid 6-digit pincode
        pincode = Pincode.objects.create(
            state=state,
            city=city,
            code='282001',
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(pincode.code, '282001')
        
        # Invalid pincodes should raise ValidationError
        invalid_codes = ['12345', '1234567', 'ABCDEF', '12A345']
        
        for invalid_code in invalid_codes:
            with self.assertRaises(ValidationError):
                invalid_pincode = Pincode(
                    state=state,
                    city=city,
                    code=invalid_code,
                    created_by=self.user,
                    updated_by=self.user
                )
                invalid_pincode.full_clean()


class GeoCascadeSignalTests(TestCase):
    """Test cascade deactivation signal behaviors."""
    
    def setUp(self):
        """Create test data hierarchy."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test hierarchy
        self.state = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.city1 = City.objects.create(
            state=self.state,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.city2 = City.objects.create(
            state=self.state,
            name='Lucknow',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.pincode1 = Pincode.objects.create(
            state=self.state,
            city=self.city1,
            code='282001',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.pincode2 = Pincode.objects.create(
            state=self.state,
            city=self.city1,
            code='282002',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.pincode3 = Pincode.objects.create(
            state=self.state,
            city=self.city2,
            code='226001',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_state_cascade_deactivation(self):
        """Test State deactivation cascades to all Cities and Pincodes."""
        # All should be active initially
        self.assertTrue(self.state.is_active)
        self.assertTrue(self.city1.is_active)
        self.assertTrue(self.city2.is_active)
        self.assertTrue(self.pincode1.is_active)
        self.assertTrue(self.pincode2.is_active)
        self.assertTrue(self.pincode3.is_active)
        
        # Deactivate state
        self.state.is_active = False
        self.state.save()
        
        # Refresh from database
        self.city1.refresh_from_db()
        self.city2.refresh_from_db()
        self.pincode1.refresh_from_db()
        self.pincode2.refresh_from_db()
        self.pincode3.refresh_from_db()
        
        # All cities and pincodes should be deactivated
        self.assertFalse(self.city1.is_active)
        self.assertFalse(self.city2.is_active)
        self.assertFalse(self.pincode1.is_active)
        self.assertFalse(self.pincode2.is_active)
        self.assertFalse(self.pincode3.is_active)
    
    def test_city_cascade_deactivation(self):
        """Test City deactivation cascades to its Pincodes only."""
        # All should be active initially
        self.assertTrue(self.city1.is_active)
        self.assertTrue(self.city2.is_active)
        self.assertTrue(self.pincode1.is_active)
        self.assertTrue(self.pincode2.is_active)
        self.assertTrue(self.pincode3.is_active)
        
        # Deactivate city1
        self.city1.is_active = False
        self.city1.save()
        
        # Refresh from database
        self.city2.refresh_from_db()
        self.pincode1.refresh_from_db()
        self.pincode2.refresh_from_db()
        self.pincode3.refresh_from_db()
        
        # Only city1's pincodes should be deactivated
        self.assertTrue(self.city2.is_active)  # Other city unaffected
        self.assertFalse(self.pincode1.is_active)  # City1's pincode
        self.assertFalse(self.pincode2.is_active)  # City1's pincode
        self.assertTrue(self.pincode3.is_active)   # City2's pincode unaffected


class GeoAuditFieldAdminTests(TestCase):
    """Test audit field functionality in admin context."""
    
    def setUp(self):
        """Create test user and admin client."""
        self.user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.user)
    
    def test_audit_fields_readonly_in_admin(self):
        """Test that audit fields are properly configured as read-only in admin."""
        from geo.admin import StateAdmin, CityAdmin, PincodeAdmin
        
        # Check that audit fields are in readonly_fields
        expected_readonly = ('created_at', 'updated_at', 'created_by', 'updated_by')
        
        self.assertEqual(StateAdmin.readonly_fields, expected_readonly)
        self.assertEqual(CityAdmin.readonly_fields, expected_readonly)
        self.assertEqual(PincodeAdmin.readonly_fields, expected_readonly)
    
    def test_admin_save_model_sets_audit_fields(self):
        """Test that admin save_model method properly sets audit fields."""
        from geo.admin import StateAdmin
        from django.contrib.admin.sites import AdminSite
        from django.http import HttpRequest
        
        # Create mock request
        request = HttpRequest()
        request.user = self.user
        
        # Create admin instance
        site = AdminSite()
        admin = StateAdmin(State, site)
        
        # Test creating new object
        state = State(code='TEST', name='Test State')
        admin.save_model(request, state, None, change=False)
        
        # Verify audit fields are set
        self.assertEqual(state.created_by, self.user)
        self.assertEqual(state.updated_by, self.user)
        
        # Test updating existing object
        different_user = User.objects.create_user(
            username='different_user',
            email='different@example.com',
            password='testpass123'
        )
        request.user = different_user
        
        admin.save_model(request, state, None, change=True)
        
        # Verify only updated_by changed
        self.assertEqual(state.created_by, self.user)  # Should remain original
        self.assertEqual(state.updated_by, different_user)  # Should be updated