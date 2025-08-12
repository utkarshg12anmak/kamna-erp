from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from catalog.models import Brand, Category, UoM, TaxRate, Item
from .models import Warehouse, Location, LocationType, VirtualSubtype, StockLedger, MovementType
from .services_putaway import post_actions
from .services_internal_move import InternalMoveLine, post_internal_move


class PutawayLostBehaviorTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username='tester', is_staff=True)
        # Catalog basics
        self.brand = Brand.objects.create(name='B')
        self.root_cat = Category.objects.create(name='Root')
        self.child_cat = Category.objects.create(name='Child', parent=self.root_cat)
        self.uom = UoM.objects.create(code='EA', name='Each', ratio_to_base=1, base=True)
        self.tax = TaxRate.objects.create(name='GST0', percent=0)
        self.item = Item.objects.create(
            name='Sample', product_type='GOODS', brand=self.brand, category=self.child_cat,
            uom=self.uom, tax_rate=self.tax, status='ACTIVE'
        )
        # Warehouse and locations (signals create virtual bins)
        self.wh = Warehouse.objects.create(
            code='W1', name='WH', status='ACTIVE', gstin='27ABCDE1234F1Z5',
            address_line1='', address_line2='', city='X', state='Y', pincode='123456', country='India',
            latitude=0, longitude=0
        )
        self.phys = Location.objects.create(warehouse=self.wh, type=LocationType.PHYSICAL, code='A1', display_name='A1')
        # Resolve virtuals
        self.return_bin = Location.objects.get(warehouse=self.wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.RETURN)
        self.lost_bin = Location.objects.get(warehouse=self.wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.LOST)
        # Seed stock in RETURN
        StockLedger.objects.create(warehouse=self.wh, location=self.return_bin, item=self.item, qty_delta=Decimal('10'), movement_type=MovementType.TRANSFER, ref_model='SEED')

    def _bal(self, loc):
        from django.db.models import Sum
        return StockLedger.objects.filter(warehouse=self.wh, location=loc, item=self.item).aggregate(Sum('qty_delta'))['qty_delta__sum'] or Decimal('0')

    def test_lost_actions_merge_into_single_pair(self):
        # Two LOST actions from same (item, source_bin) should merge, creating exactly 2 ledger rows (out from src, in to LOST)
        actions = [
            {'type':'LOST','item':self.item.id,'source_bin':self.return_bin.id,'qty':Decimal('2')},
            {'type':'LOST','item':self.item.id,'source_bin':self.return_bin.id,'qty':Decimal('1')},
        ]
        result = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id='test-batch-1')
        self.assertEqual(result['posted_count'], 1)
        # Exactly one pair with the batch ref
        rows = StockLedger.objects.filter(warehouse=self.wh, ref_model='PUTAWAY', ref_id='test-batch-1', movement_type=MovementType.PUTAWAY_LOST)
        self.assertEqual(rows.count(), 2)
        # Balances updated by total qty=3
        self.assertEqual(self._bal(self.return_bin), Decimal('7'))
        self.assertEqual(self._bal(self.lost_bin), Decimal('3'))

    def test_idempotency_prevents_duplicate_postings(self):
        actions = [{'type':'LOST','item':self.item.id,'source_bin':self.return_bin.id,'qty':Decimal('4')}]
        first = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id='dup-key-1')
        self.assertEqual(first['posted_count'], 1)
        again = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id='dup-key-1')
        self.assertEqual(again['posted_count'], 0)
        self.assertTrue(again.get('duplicate'))
        rows = StockLedger.objects.filter(warehouse=self.wh, ref_model='PUTAWAY', ref_id='dup-key-1', movement_type=MovementType.PUTAWAY_LOST)
        self.assertEqual(rows.count(), 2)

    def test_multiple_sequential_putaway_lost_postings(self):
        actions = [{'type':'LOST','item':self.item.id,'source_bin':self.return_bin.id,'qty':Decimal('4')}]
        first = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id='batch-1')
        self.assertEqual(first['posted_count'], 1)
        # Posting again with the same batch_ref_id should not create duplicates
        second = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id='batch-1')
        self.assertEqual(second['posted_count'], 0)
        self.assertTrue(second.get('duplicate'))
        rows = StockLedger.objects.filter(warehouse=self.wh, ref_model='PUTAWAY', ref_id='batch-1', movement_type=MovementType.PUTAWAY_LOST)
        self.assertEqual(rows.count(), 2)
        # Using a new batch_ref_id should create new postings
        third = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id='batch-2')
        self.assertEqual(third['posted_count'], 1)
        rows = StockLedger.objects.filter(warehouse=self.wh, ref_model='PUTAWAY', ref_id='batch-2', movement_type=MovementType.PUTAWAY_LOST)
        self.assertEqual(rows.count(), 2)


class InternalMoveTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username='mover', is_staff=True)
        # Catalog basics
        self.brand = Brand.objects.create(name='B')
        self.root_cat = Category.objects.create(name='Root')
        self.child_cat = Category.objects.create(name='Child', parent=self.root_cat)
        self.uom = UoM.objects.create(code='EA', name='Each', ratio_to_base=1, base=True)
        self.tax = TaxRate.objects.create(name='GST0', percent=0)
        self.item = Item.objects.create(
            name='IM Item', product_type='GOODS', brand=self.brand, category=self.child_cat,
            uom=self.uom, tax_rate=self.tax, status='ACTIVE'
        )
        # Warehouse and locations
        self.wh = Warehouse.objects.create(
            code='W2', name='WH2', status='ACTIVE', gstin='27ABCDE1234F1Z6',
            address_line1='', address_line2='', city='X', state='Y', pincode='123456', country='India',
            latitude=0, longitude=0
        )
        self.src = Location.objects.create(warehouse=self.wh, type=LocationType.PHYSICAL, code='A1', display_name='A1')
        self.dst = Location.objects.create(warehouse=self.wh, type=LocationType.PHYSICAL, code='B1', display_name='B1')
        # Seed stock at source
        StockLedger.objects.create(warehouse=self.wh, location=self.src, item=self.item, qty_delta=Decimal('10'), movement_type=MovementType.TRANSFER, ref_model='SEED')

    def _bal(self, loc):
        from django.db.models import Sum
        return StockLedger.objects.filter(warehouse=self.wh, location=loc, item=self.item).aggregate(Sum('qty_delta'))['qty_delta__sum'] or Decimal('0')

    def test_merge_and_post(self):
        lines = [
            InternalMoveLine(item_id=self.item.id, source_location_id=self.src.id, target_location_id=self.dst.id, qty=Decimal('2')),
            InternalMoveLine(item_id=self.item.id, source_location_id=self.src.id, target_location_id=self.dst.id, qty=Decimal('3')),
        ]
        res = post_internal_move(self.user, lines, batch_ref_id='im-merge-1')
        self.assertEqual(res['posted'], 2)  # one out, one in
        rows = StockLedger.objects.filter(warehouse=self.wh, ref_model='INTERNAL_MOVE', ref_id='im-merge-1', movement_type=MovementType.INTERNAL_TRANSFER)
        self.assertEqual(rows.count(), 2)
        self.assertEqual(self._bal(self.src), Decimal('5'))
        self.assertEqual(self._bal(self.dst), Decimal('5'))

    def test_idempotency_duplicate(self):
        line = InternalMoveLine(item_id=self.item.id, source_location_id=self.src.id, target_location_id=self.dst.id, qty=Decimal('4'))
        first = post_internal_move(self.user, [line], batch_ref_id='im-dup-1')
        self.assertEqual(first['posted'], 2)
        again = post_internal_move(self.user, [line], batch_ref_id='im-dup-1')
        self.assertEqual(again['posted'], 0)
        self.assertTrue(again.get('duplicate'))
        rows = StockLedger.objects.filter(warehouse=self.wh, ref_model='INTERNAL_MOVE', ref_id='im-dup-1', movement_type=MovementType.INTERNAL_TRANSFER)
        self.assertEqual(rows.count(), 2)

    def test_insufficient_stock_validation(self):
        line = InternalMoveLine(item_id=self.item.id, source_location_id=self.src.id, target_location_id=self.dst.id, qty=Decimal('100'))
        with self.assertRaises(Exception):
            post_internal_move(self.user, [line], batch_ref_id='im-fail-1')

    def test_must_be_physical_and_same_warehouse(self):
        # Use a virtual bin from this warehouse; signals created them
        from .models import VirtualSubtype
        return_bin = Location.objects.get(warehouse=self.wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.RETURN)
        line = InternalMoveLine(item_id=self.item.id, source_location_id=return_bin.id, target_location_id=self.dst.id, qty=Decimal('1'))
        with self.assertRaises(Exception):
            post_internal_move(self.user, [line], batch_ref_id='im-virt-1')
        # Different warehouse location
        wh2 = Warehouse.objects.create(
            code='W3', name='WH3', status='ACTIVE', gstin='27ABCDE1234F1Z7',
            address_line1='', address_line2='', city='X', state='Y', pincode='123456', country='India',
            latitude=0, longitude=0
        )
        other_loc = Location.objects.create(warehouse=wh2, type=LocationType.PHYSICAL, code='Z1', display_name='Z1')
        line2 = InternalMoveLine(item_id=self.item.id, source_location_id=self.src.id, target_location_id=other_loc.id, qty=Decimal('1'))
        with self.assertRaises(Exception):
            post_internal_move(self.user, [line2], batch_ref_id='im-crosswh-1')


class PutawayConcurrencyTests(TransactionTestCase):
    reset_sequences = True
    def setUp(self):
        from django.db import connection
        User = get_user_model()
        self.user = User.objects.create(username='concurrent', is_staff=True)
        self.brand = Brand.objects.create(name='B')
        self.root = Category.objects.create(name='RootC')
        self.child = Category.objects.create(name='ChildC', parent=self.root)
        self.uom = UoM.objects.create(code='EA', name='Each', ratio_to_base=1, base=True)
        self.tax = TaxRate.objects.create(name='GST0', percent=0)
        self.item = Item.objects.create(name='CItem', product_type='GOODS', brand=self.brand, category=self.child, uom=self.uom, tax_rate=self.tax, status='ACTIVE')
        self.wh = Warehouse.objects.create(code='W4', name='WH4', status='ACTIVE', gstin='27ABCDE1234F1Z8', address_line1='', address_line2='', city='X', state='Y', pincode='123456', country='India', latitude=0, longitude=0)
        self.return_bin = Location.objects.get(warehouse=self.wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.RETURN)
        StockLedger.objects.create(warehouse=self.wh, location=self.return_bin, item=self.item, qty_delta=Decimal('20'), movement_type=MovementType.TRANSFER, ref_model='SEED')
        # Ensure commit so spawned threads can see data
        connection.commit()

    def test_concurrent_lost_single_pair(self):
        actions = [{'type':'LOST','item':self.item.id,'source_bin':self.return_bin.id,'qty':Decimal('5')}]
        results = []
        import threading
        def worker():
            from .services_putaway import post_actions
            res = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id=None)
            results.append(res)
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        successes = [r for r in results if r['posted_count'] == 1]
        duplicates = [r for r in results if r.get('duplicate')]
        self.assertEqual(len(successes), 1, f"Expected exactly one success, got {results}")
        self.assertTrue(len(duplicates) >= 4)
        ref = successes[0]['batch_ref_id']
        lost_rows = StockLedger.objects.filter(warehouse=self.wh, ref_model='PUTAWAY', ref_id=ref, movement_type=MovementType.PUTAWAY_LOST)
        self.assertEqual(lost_rows.count(), 2)

    def test_client_idempotency_key_prevents_duplicates(self):
        """Test that client-provided idempotency keys prevent duplicate postings"""
        actions = [{'type':'LOST','item':self.item.id,'source_bin':self.return_bin.id,'qty':Decimal('3')}]
        client_key = 'client:test-session-123:12345'
        
        # First request with client key
        first = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id=client_key)
        self.assertEqual(first['posted_count'], 1)
        self.assertEqual(first['batch_ref_id'], client_key)
        
        # Second request with same client key should be treated as duplicate
        second = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id=client_key)
        self.assertEqual(second['posted_count'], 0)
        self.assertTrue(second.get('duplicate'))
        self.assertEqual(second['batch_ref_id'], client_key)
        
        # Verify only one set of ledger entries exists
        rows = StockLedger.objects.filter(warehouse=self.wh, ref_model='PUTAWAY', ref_id=client_key, movement_type=MovementType.PUTAWAY_LOST)
        self.assertEqual(rows.count(), 2)

    def test_concurrent_lost_with_client_keys(self):
        """Test concurrent requests with same client idempotency key"""
        actions = [{'type':'LOST','item':self.item.id,'source_bin':self.return_bin.id,'qty':Decimal('2')}]
        client_key = 'client:concurrent-test:98765'
        results = []
        import threading
        
        def worker():
            from .services_putaway import post_actions
            res = post_actions(self.wh, actions, user=self.user, reason_map=None, batch_ref_id=client_key)
            results.append(res)
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        
        successes = [r for r in results if r['posted_count'] == 1]
        duplicates = [r for r in results if r.get('duplicate')]
        
        # Should have exactly one success and the rest duplicates
        self.assertEqual(len(successes), 1, f"Expected exactly one success, got {results}")
        self.assertTrue(len(duplicates) >= 4)
        
        # Verify all results have the same ref_id
        for result in results:
            self.assertEqual(result['batch_ref_id'], client_key)
        
        # Verify only one set of ledger entries exists
        lost_rows = StockLedger.objects.filter(warehouse=self.wh, ref_model='PUTAWAY', ref_id=client_key, movement_type=MovementType.PUTAWAY_LOST)
        self.assertEqual(lost_rows.count(), 2)
