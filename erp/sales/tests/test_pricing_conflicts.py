from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date
from geo.models import State, City, Pincode, Territory, TerritoryMember, TerritoryCoverage
from catalog.models import Brand, Category, TaxRate, UoM, Item
from sales.models import PriceList, PriceListItem, PriceListTier, PriceListStatus, PriceCoverage

class PricingConflictTestCase(TestCase):
    def setUp(self):
        # Create test geo data
        self.state = State.objects.create(code='DL', name='Delhi')
        self.city = City.objects.create(state=self.state, name='New Delhi')
        self.pincode1 = Pincode.objects.create(state=self.state, city=self.city, code='110001')
        self.pincode2 = Pincode.objects.create(state=self.state, city=self.city, code='110002')
        
        # Create territory and coverage
        self.territory = Territory.objects.create(code='T_DELHI', name='Delhi Territory', type='PINCODE')
        TerritoryMember.objects.create(territory=self.territory, pincode=self.pincode1)
        
        # Create catalog items
        self.brand = Brand.objects.create(name='Test Brand')
        # Create parent category first, then child category (for GOODS validation)
        self.parent_category = Category.objects.create(name='Parent Category')
        self.category = Category.objects.create(name='Test Category', parent=self.parent_category)
        self.tax_rate = TaxRate.objects.create(name='GST 18%', percent=18.0)
        # Create UoM for GOODS items
        self.uom = UoM.objects.create(code='PCS', name='Pieces', ratio_to_base=1.0, base=True)
        self.item1 = Item.objects.create(
            name='Test Item 1', brand=self.brand, 
            category=self.category, tax_rate=self.tax_rate, uom=self.uom
        )
        self.item2 = Item.objects.create(
            name='Test Item 2', brand=self.brand,
            category=self.category, tax_rate=self.tax_rate, uom=self.uom
        )

    def test_same_item_overlapping_dates_causes_conflict(self):
        """Test that same item in two lists with overlapping dates causes ValidationError"""
        # Create first price list
        pl1 = PriceList.objects.create(
            code='PL001', name='Price List 1', territory=self.territory,
            effective_from=date(2024, 1, 1), effective_till=date(2024, 12, 31)
        )
        PriceListItem.objects.create(price_list=pl1, item=self.item1)
        
        # Try to create second price list with overlapping dates and same item
        pl2 = PriceList.objects.create(
            code='PL002', name='Price List 2', territory=self.territory,
            effective_from=date(2024, 6, 1), effective_till=date(2024, 12, 31)
        )
        
        with self.assertRaises(ValidationError):
            PriceListItem.objects.create(price_list=pl2, item=self.item1)

    def test_archiving_one_list_allows_the_other(self):
        """Test that archiving one conflicting list allows the other to be created"""
        # Create first price list
        pl1 = PriceList.objects.create(
            code='PL001', name='Price List 1', territory=self.territory,
            effective_from=date(2024, 1, 1), effective_till=date(2024, 12, 31)
        )
        PriceListItem.objects.create(price_list=pl1, item=self.item1)
        
        # Archive the first list
        pl1.status = PriceListStatus.ARCHIVED
        pl1.save()
        
        # Now creating second list should work
        pl2 = PriceList.objects.create(
            code='PL002', name='Price List 2', territory=self.territory,
            effective_from=date(2024, 6, 1), effective_till=date(2024, 12, 31)
        )
        # This should not raise an exception
        PriceListItem.objects.create(price_list=pl2, item=self.item1)

    def test_non_overlapping_windows_allows_both(self):
        """Test that non-overlapping date windows allow both lists"""
        # Create first price list
        pl1 = PriceList.objects.create(
            code='PL001', name='Price List 1', territory=self.territory,
            effective_from=date(2024, 1, 1), effective_till=date(2024, 6, 30)
        )
        PriceListItem.objects.create(price_list=pl1, item=self.item1)
        
        # Create second price list with non-overlapping dates
        pl2 = PriceList.objects.create(
            code='PL002', name='Price List 2', territory=self.territory,
            effective_from=date(2024, 7, 1), effective_till=date(2024, 12, 31)
        )
        # This should not raise an exception
        PriceListItem.objects.create(price_list=pl2, item=self.item1)

    def test_tier_validation_max_qty_required(self):
        """Test that first tier must have max_qty>=1 unless open-ended"""
        pl = PriceList.objects.create(
            code='PL001', name='Price List 1', territory=self.territory
        )
        pli = PriceListItem.objects.create(price_list=pl, item=self.item1)
        
        # This should fail - max_qty < 1 and not open-ended
        tier = PriceListTier(price_list_item=pli, max_qty=0, min_unit_price=100.00, is_open_ended=False)
        with self.assertRaises(ValidationError):
            tier.full_clean()

    def test_open_ended_tier_allowed(self):
        """Test that open-ended tier is allowed"""
        pl = PriceList.objects.create(
            code='PL001', name='Price List 1', territory=self.territory
        )
        pli = PriceListItem.objects.create(price_list=pl, item=self.item1)
        
        # This should work - open-ended tier
        tier = PriceListTier(price_list_item=pli, max_qty=None, min_unit_price=100.00, is_open_ended=True)
        tier.full_clean()  # Should not raise an exception
