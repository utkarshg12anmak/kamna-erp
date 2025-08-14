from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from decimal import Decimal

from catalog.models import Item, Category, UoM
from warehousing.models import Warehouse
from ..models import STN, STNDetail, STNStatus
from ..api.errors import (
    SKU_DUPLICATE, QTY_EXCEEDS_AVAILABLE, INVALID_STATE_CHANGE,
    SOFT_DELETE_NOT_ALLOWED, CONFIRM_FAILED, WAREHOUSES_SAME
)


class STNAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test warehouses
        self.warehouse_a = Warehouse.objects.create(
            name='Warehouse A', 
            code='WH-A',
            latitude=0.0,
            longitude=0.0
        )
        self.warehouse_b = Warehouse.objects.create(
            name='Warehouse B', 
            code='WH-B',
            latitude=0.0,
            longitude=0.0
        )
        
        # Create test SKU
        parent_category = Category.objects.create(name='Parent Category')
        child_category = Category.objects.create(name='Child Category', parent=parent_category)
        uom = UoM.objects.create(code='KG', name='Kilogram')
        self.sku = Item.objects.create(
            name='Test SKU',
            category=child_category,
            uom=uom,
            product_type='GOODS'
        )

    def test_create_stn_draft(self):
        """Test creating a STN in DRAFT status"""
        data = {
            'source_warehouse': self.warehouse_a.id,
            'destination_warehouse': self.warehouse_b.id,
            'notes': 'Test STN'
        }
        response = self.client.post('/api/inventory/stns/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], STNStatus.DRAFT)
        self.assertIsNotNone(response.data['stn_code'])

    def test_add_line_duplicate_sku_fails(self):
        """Test adding same SKU twice to STN returns sku_duplicate error"""
        # Create STN
        stn = STN.objects.create(
            source_warehouse=self.warehouse_a,
            destination_warehouse=self.warehouse_b,
            created_by=self.user
        )
        
        # Add first line
        with patch('inventory_management.api.serializers.get_available_physical_qty', return_value=Decimal('100')):
            data = {
                'stn': stn.id,
                'sku': self.sku.id,
                'created_qty': '10'
            }
            response = self.client.post('/api/inventory/stn_lines/', data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to add same SKU again
        with patch('inventory_management.api.serializers.get_available_physical_qty', return_value=Decimal('100')):
            response = self.client.post('/api/inventory/stn_lines/', data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['sku']['code'], SKU_DUPLICATE)

    def test_add_line_qty_exceeds_available(self):
        """Test adding line with qty > available returns qty_exceeds_available error"""
        stn = STN.objects.create(
            source_warehouse=self.warehouse_a,
            destination_warehouse=self.warehouse_b,
            created_by=self.user
        )
        
        with patch('inventory_management.api.serializers.get_available_physical_qty', return_value=Decimal('5')):
            data = {
                'stn': stn.id,
                'sku': self.sku.id,
                'created_qty': '10'  # More than available (5)
            }
            response = self.client.post('/api/inventory/stn_lines/', data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['created_qty']['code'], QTY_EXCEEDS_AVAILABLE)

    def test_confirm_revalidates_and_returns_shortages(self):
        """Test confirm action re-checks availability and returns shortages on failure"""
        stn = STN.objects.create(
            source_warehouse=self.warehouse_a,
            destination_warehouse=self.warehouse_b,
            created_by=self.user,
            status=STNStatus.DRAFT
        )
        
        # Add line with sufficient availability initially
        with patch('inventory_management.api.serializers.get_available_physical_qty', return_value=Decimal('100')):
            STNDetail.objects.create(stn=stn, sku=self.sku, created_qty=Decimal('50'))
        
        # Mock reduced availability during confirm
        with patch('inventory_management.api.views.get_available_physical_qty', return_value=Decimal('30')):
            response = self.client.post(f'/api/inventory/stns/{stn.id}/confirm/')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['code'], CONFIRM_FAILED)
            self.assertIn('shortages', response.data)
            self.assertEqual(len(response.data['shortages']), 1)
            shortage = response.data['shortages'][0]
            self.assertEqual(shortage['sku_id'], self.sku.id)
            self.assertEqual(shortage['need'], 50.0)
            self.assertEqual(shortage['have'], 30.0)
            self.assertEqual(shortage['short_by'], 20.0)

    def test_soft_delete_works_only_when_created_and_no_dispatch(self):
        """Test soft_delete only works for CREATED status with no dispatches"""
        stn = STN.objects.create(
            source_warehouse=self.warehouse_a,
            destination_warehouse=self.warehouse_b,
            created_by=self.user,
            status=STNStatus.DRAFT
        )
        
        # Try soft delete on DRAFT - should fail
        response = self.client.post(f'/api/inventory/stns/{stn.id}/soft_delete/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], SOFT_DELETE_NOT_ALLOWED)
        
        # Change to CREATED
        stn.status = STNStatus.CREATED
        stn.save()
        
        # Should work now
        response = self.client.post(f'/api/inventory/stns/{stn.id}/soft_delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stn.refresh_from_db()
        self.assertEqual(stn.status, STNStatus.DELETED)
        
        # Test with dispatched quantity
        stn2 = STN.objects.create(
            source_warehouse=self.warehouse_a,
            destination_warehouse=self.warehouse_b,
            created_by=self.user,
            status=STNStatus.CREATED,
            sum_dispatched_qty=Decimal('10')
        )
        
        response = self.client.post(f'/api/inventory/stns/{stn2.id}/soft_delete/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], SOFT_DELETE_NOT_ALLOWED)

    def test_editing_non_draft_returns_invalid_state_change(self):
        """Test editing non-DRAFT STN returns INVALID_STATE_CHANGE error"""
        stn = STN.objects.create(
            source_warehouse=self.warehouse_a,
            destination_warehouse=self.warehouse_b,
            created_by=self.user,
            status=STNStatus.CREATED
        )
        
        data = {'notes': 'Updated notes'}
        response = self.client.patch(f'/api/inventory/stns/{stn.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], INVALID_STATE_CHANGE)

    def test_list_supports_filters_and_search(self):
        """Test STN list supports filters and search"""
        # Create test STNs
        stn1 = STN.objects.create(
            source_warehouse=self.warehouse_a,
            destination_warehouse=self.warehouse_b,
            created_by=self.user,
            status=STNStatus.DRAFT
        )
        stn2 = STN.objects.create(
            source_warehouse=self.warehouse_b,
            destination_warehouse=self.warehouse_a,
            created_by=self.user,
            status=STNStatus.CREATED
        )
        
        # Test status filter
        response = self.client.get('/api/inventory/stns/?status=DRAFT')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], stn1.id)
        
        # Test warehouse filter
        response = self.client.get(f'/api/inventory/stns/?source_warehouse={self.warehouse_a.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], stn1.id)
        
        # Test search by STN code
        response = self.client.get(f'/api/inventory/stns/?search={stn1.stn_code}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], stn1.id)
