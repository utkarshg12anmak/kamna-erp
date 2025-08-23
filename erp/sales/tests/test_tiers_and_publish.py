from django.test import TestCase
from django.core.exceptions import ValidationError
from sales.tests.utils import make_geo_simple, make_item, make_pricelist, add_item_with_tiers
from sales.models import PriceListStatus

class PriceTiersAndPublishTest(TestCase):
    def setUp(self):
        *_, self.territory = make_geo_simple()
        self.item = make_item()

    def test_valid_tiers_then_publish(self):
        pl = make_pricelist(self.territory, code='PL-A', status=PriceListStatus.DRAFT)
        add_item_with_tiers(pl, self.item, [
            {'max_qty': 10, 'min_unit_price': '100.00', 'is_open_ended': False},
            {'max_qty': None, 'min_unit_price': '90.00', 'is_open_ended': True}
        ])
        pl.status = PriceListStatus.PUBLISHED
        pl.full_clean(); pl.save(update_fields=['status'])
        self.assertEqual(pl.status, PriceListStatus.PUBLISHED)

    def test_openended_not_last_is_rejected(self):
        pl = make_pricelist(self.territory, code='PL-B')
        # open-ended first
        with self.assertRaises(ValidationError):
            add_item_with_tiers(pl, self.item, [
                {'max_qty': None, 'min_unit_price': '90.00', 'is_open_ended': True},
                {'max_qty': 10, 'min_unit_price': '100.00', 'is_open_ended': False}
            ])
