from django.test import TestCase
from sales.models import PriceListItem, PriceListTier, PriceList
from sales.services import resolve_min_unit_price_for_qty

class PriceListTierResolverTest(TestCase):
    def setUp(self):
        pl = PriceList.objects.create(code="PL1", status="active")
        self.pli = PriceListItem.objects.create(price_list=pl, item_id=1)
        # Tiers: 10 @ 100, 20 @ 90, open-ended @ 80
        PriceListTier.objects.create(item=self.pli, max_qty=10, min_unit_price=100)
        PriceListTier.objects.create(item=self.pli, max_qty=20, min_unit_price=90)
        PriceListTier.objects.create(item=self.pli, is_open_ended=True, min_unit_price=80)

    def test_tier_for_low_qty(self):
        tier, price, warning = resolve_min_unit_price_for_qty(self.pli, 5)
        self.assertEqual(price, 100)
        self.assertEqual(tier.max_qty, 10)
        self.assertIsNone(warning)

    def test_tier_for_mid_qty(self):
        tier, price, warning = resolve_min_unit_price_for_qty(self.pli, 15)
        self.assertEqual(price, 90)
        self.assertEqual(tier.max_qty, 20)
        self.assertIsNone(warning)

    def test_tier_for_high_qty(self):
        tier, price, warning = resolve_min_unit_price_for_qty(self.pli, 100)
        self.assertEqual(price, 80)
        self.assertTrue(tier.is_open_ended)
        self.assertIsNone(warning)

    def test_warning_on_non_increasing(self):
        # Add a tier with a lower max_qty than previous
        PriceListTier.objects.create(item=self.pli, max_qty=5, min_unit_price=110)
        tier, price, warning = resolve_min_unit_price_for_qty(self.pli, 3)
        self.assertIsNotNone(warning)
        self.assertIn("non-increasing", warning)

    def test_no_tiers(self):
        pli2 = PriceListItem.objects.create(price_list=self.pli.price_list, item_id=2)
        tier, price, warning = resolve_min_unit_price_for_qty(pli2, 1)
        self.assertIsNone(tier)
        self.assertIsNone(price)
        self.assertIsNone(warning)
