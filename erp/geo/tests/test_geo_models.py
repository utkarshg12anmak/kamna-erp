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
    
    def test_state_unique_name(self):
        """Test State name uniqueness constraint."""
        State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should raise IntegrityError for duplicate name
        with self.assertRaises(IntegrityError):
            State.objects.create(
                code='UK',
                name='Uttar Pradesh',
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
    
    def test_city_unique_per_state(self):
        """Test City name uniqueness per state."""
        state1 = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        state2 = State.objects.create(
            code='MP',
            name='Madhya Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create city in first state
        City.objects.create(
            state=state1,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Same city name in different state should be allowed
        city2 = City.objects.create(
            state=state2,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(city2.name, 'Agra')
        
        # Same city name in same state should raise IntegrityError
        with self.assertRaises(IntegrityError):
            City.objects.create(
                state=state1,
                name='Agra',
                created_by=self.user,
                updated_by=self.user
            )
    
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
                invalid_pincode.clean()
    
    def test_pincode_city_state_consistency(self):
        """Test Pincode city-state consistency validation."""
        state1 = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        state2 = State.objects.create(
            code='MP',
            name='Madhya Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        city = City.objects.create(
            state=state1,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        
        # City belongs to state1, but pincode tries to use state2
        with self.assertRaises(ValidationError):
            invalid_pincode = Pincode(
                state=state2,  # Wrong state
                city=city,     # City belongs to state1
                code='282001',
                created_by=self.user,
                updated_by=self.user
            )
            invalid_pincode.clean()
    
    def test_pincode_global_uniqueness(self):
        """Test Pincode global uniqueness constraint."""
        state1 = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        state2 = State.objects.create(
            code='MP',
            name='Madhya Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        city1 = City.objects.create(
            state=state1,
            name='Agra',
            created_by=self.user,
            updated_by=self.user
        )
        city2 = City.objects.create(
            state=state2,
            name='Indore',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create pincode in first location
        Pincode.objects.create(
            state=state1,
            city=city1,
            code='282001',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Same pincode in different location should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Pincode.objects.create(
                state=state2,
                city=city2,
                code='282001',  # Duplicate pincode
                created_by=self.user,
                updated_by=self.user
            )


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
    
    def test_activation_no_cascade(self):
        """Test that activation does not cascade (one-way cascade)."""
        # Deactivate state (cascades to all)
        self.state.is_active = False
        self.state.save()
        
        # Refresh all
        self.city1.refresh_from_db()
        self.pincode1.refresh_from_db()
        
        # All should be inactive
        self.assertFalse(self.city1.is_active)
        self.assertFalse(self.pincode1.is_active)
        
        # Reactivate state
        self.state.is_active = True
        self.state.save()
        
        # Refresh all
        self.city1.refresh_from_db()
        self.pincode1.refresh_from_db()
        
        # Children should remain inactive (no cascade on activation)
        self.assertFalse(self.city1.is_active)
        self.assertFalse(self.pincode1.is_active)
    
    def test_no_cascade_if_already_inactive(self):
        """Test no unnecessary cascade if children already inactive."""
        # Manually deactivate a pincode
        self.pincode1.is_active = False
        self.pincode1.save()
        
        # Deactivate city (should not affect already inactive pincode)
        self.city1.is_active = False
        self.city1.save()
        
        # Refresh
        self.pincode1.refresh_from_db()
        self.pincode2.refresh_from_db()
        
        # Both should be inactive, but pincode1 was already inactive
        self.assertFalse(self.pincode1.is_active)
        self.assertFalse(self.pincode2.is_active)


class GeoAuditTrailTests(TestCase):
    """Test audit trail functionality."""
    
    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_state_history_tracking(self):
        """Test State history tracking with simple_history."""
        state = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Check history record created
        self.assertEqual(state.history.count(), 1)
        
        # Update state
        state.name = 'Uttar Pradesh Updated'
        state.save()
        
        # Check history record for update
        self.assertEqual(state.history.count(), 2)
        
        # Check history content
        latest_history = state.history.first()
        self.assertEqual(latest_history.name, 'Uttar Pradesh Updated')
    
    def test_audit_fields_populated(self):
        """Test audit fields are properly populated."""
        state = State.objects.create(
            code='UP',
            name='Uttar Pradesh',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Check audit fields
        self.assertEqual(state.created_by, self.user)
        self.assertEqual(state.updated_by, self.user)
        self.assertIsNotNone(state.created_at)
        self.assertIsNotNone(state.updated_at)
