from django.test import TestCase
from django.core.exceptions import ValidationError
from geo.models import State, City, Pincode, Territory, TerritoryMember
from sales.models import PriceList, PriceListItem, PriceListTier, PriceListStatus
from catalog.models import Item

class PriceListTierRulesTest(TestCase):
    def setUp(self):
        s = State.objects.create(code='DL', name='Delhi', is_active=True)
        c = City.objects.create(state=s, name='New Delhi', is_active=True)
        p = Pincode.objects.create(state=s, city=c, code='110001', is_active=True)
        t = Territory.objects.create(code='NCR-001', name='NCR Core', type='PINCODE')
        TerritoryMember.objects.create(territory=t, pincode=p)
        self.pl = PriceList.objects.create(code='PL-TIER', name='Tier List', territory=t, status=PriceListStatus.DRAFT)
        # --- Catalog requirements ---
        from catalog.models import Brand, Category, UoM, TaxRate
        self.brand = Brand.objects.create(name='Test Brand')
        self.parent_category = Category.objects.create(name='ParentCat')
        self.category = Category.objects.create(name='ChildCat', parent=self.parent_category)
        self.uom = UoM.objects.create(code='EA', name='Each', ratio_to_base=1, base=True)
        self.tax = TaxRate.objects.create(name='GST0', percent=0)
        self.item = Item.objects.create(
            name='Test A', sku='SKU0000001', product_type='GOODS', status='ACTIVE',
            brand=self.brand, category=self.category, uom=self.uom, tax_rate=self.tax
        )
        self.pli = PriceListItem.objects.create(price_list=self.pl, item=self.item)

    def test_valid_non_openended_then_openended(self):
        PriceListTier.objects.create(price_list_item=self.pli, max_qty=10, min_unit_price='100.00', is_open_ended=False)
        PriceListTier.objects.create(price_list_item=self.pli, max_qty=None, min_unit_price='90.00', is_open_ended=True)
        self.assertEqual(self.pli.tiers.count(), 2)

    def test_duplicate_max_qty_rejected(self):
        PriceListTier.objects.create(price_list_item=self.pli, max_qty=10, min_unit_price='100.00', is_open_ended=False)
        with self.assertRaises(ValidationError):
            t = PriceListTier(price_list_item=self.pli, max_qty=10, min_unit_price='99.00', is_open_ended=False)
            t.full_clean()

    def test_openended_requires_null_maxqty(self):
        with self.assertRaises(ValidationError):
            t = PriceListTier(price_list_item=self.pli, max_qty=50, min_unit_price='90.00', is_open_ended=True)
            t.full_clean()

    def test_cannot_add_non_openended_after_openended(self):
        PriceListTier.objects.create(price_list_item=self.pli, max_qty=None, min_unit_price='90.00', is_open_ended=True)
        with self.assertRaises(ValidationError):
            t = PriceListTier(price_list_item=self.pli, max_qty=100, min_unit_price='85.00', is_open_ended=False)
            t.full_clean()

    def test_publish_validates_tier_shape(self):
        PriceListTier.objects.create(price_list_item=self.pli, max_qty=5, min_unit_price='120.00', is_open_ended=False)
        PriceListTier.objects.create(price_list_item=self.pli, max_qty=None, min_unit_price='100.00', is_open_ended=True)
        self.pl.status = PriceListStatus.DRAFT
        self.pl.save()
        # mimic admin publish path: should pass without raising
        self.pl.status = PriceListStatus.PUBLISHED
        self.pl.save(update_fields=['status'])
