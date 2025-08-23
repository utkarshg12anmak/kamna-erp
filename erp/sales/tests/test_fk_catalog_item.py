from django.test import TestCase
from sales.tests.utils import make_geo_simple, make_item, make_pricelist
from sales.models import PriceListItem

class FKCatalogItemTest(TestCase):
    def test_fk_points_to_catalog_item(self):
        *_, territory = make_geo_simple()
        item = make_item(sku='SKU-ZZZ', name='Zed')
        pl = make_pricelist(territory, code='PL-FK')
        pli = PriceListItem.objects.create(price_list=pl, item=item)
        self.assertEqual(pli.item_id, item.id)
