from django.test import TestCase
from sales.tests.utils import make_geo_simple, make_item, make_pricelist, add_item_with_tiers
from sales.models import PriceCoverage, PriceListStatus

class CoverageSyncTest(TestCase):
    def setUp(self):
        *_, self.territory = make_geo_simple(pincode='110002')
        self.itemA = make_item(sku='SKU-A', name='Item A')
        self.itemB = make_item(sku='SKU-B', name='Item B')

    def test_add_remove_items_updates_coverage(self):
        pl = make_pricelist(self.territory, code='PL-COV')
        self.assertEqual(PriceCoverage.objects.filter(price_list=pl).count(), 0)
        add_item_with_tiers(pl, self.itemA, [{'max_qty': 10, 'min_unit_price': '100.00', 'is_open_ended': False}])
        self.assertGreater(PriceCoverage.objects.filter(price_list=pl, item=self.itemA).count(), 0)
        add_item_with_tiers(pl, self.itemB, [{'max_qty': 5, 'min_unit_price': '50.00', 'is_open_ended': False}])
        self.assertGreater(PriceCoverage.objects.filter(price_list=pl, item=self.itemB).count(), 0)
        # remove B
        pl.items.filter(item=self.itemB).delete()
        self.assertEqual(PriceCoverage.objects.filter(price_list=pl, item=self.itemB).count(), 0)

    def test_date_status_change_updates_coverage_rows(self):
        pl = make_pricelist(self.territory, code='PL-COV2')
        add_item_with_tiers(pl, self.itemA, [{'max_qty': 10, 'min_unit_price': '100.00', 'is_open_ended': False}])
        before = list(PriceCoverage.objects.filter(price_list=pl).values_list('status', flat=True))
        self.assertTrue(before and all(s == 'DRAFT' for s in before))
        pl.status = PriceListStatus.PUBLISHED; pl.save(update_fields=['status'])
        after = list(PriceCoverage.objects.filter(price_list=pl).values_list('status', flat=True))
        self.assertTrue(after and all(s == 'PUBLISHED' for s in after))
