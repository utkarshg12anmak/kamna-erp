from django.test import TestCase
from datetime import date
from geo.models import State, City, Pincode, Territory, TerritoryMember, TerritoryCoverage
from catalog.models import Brand, Category, TaxRate, UoM, Item
from sales.models import PriceList, PriceListItem, PriceCoverage, PriceListStatus

class PricingCoverageSyncAndFKTestCase(TestCase):
    def setUp(self):
        # Create test geo data
        self.state = State.objects.create(code='DL', name='Delhi')
        self.city = City.objects.create(state=self.state, name='New Delhi')
        self.pincode1 = Pincode.objects.create(state=self.state, city=self.city, code='110001')
        self.pincode2 = Pincode.objects.create(state=self.state, city=self.city, code='110002')
        
        # Create territory and add both pincodes
        self.territory = Territory.objects.create(code='T_DELHI', name='Delhi Territory', type='PINCODE')
        TerritoryMember.objects.create(territory=self.territory, pincode=self.pincode1)
        TerritoryMember.objects.create(territory=self.territory, pincode=self.pincode2)
        
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

    def test_adding_pricelistitem_updates_coverage_counts(self):
        """Test that adding/removing PriceListItem updates PriceCoverage counts"""
        # Create price list
        pl = PriceList.objects.create(
            code='PL001', name='Price List 1', territory=self.territory,
            effective_from=date(2024, 1, 1), effective_till=date(2024, 12, 31)
        )
        
        # Initially no coverage rows
        initial_count = PriceCoverage.objects.filter(price_list=pl).count()
        self.assertEqual(initial_count, 0)
        
        # Add first item - should create coverage for 2 pincodes
        pli1 = PriceListItem.objects.create(price_list=pl, item=self.item1)
        count_after_item1 = PriceCoverage.objects.filter(price_list=pl).count()
        self.assertEqual(count_after_item1, 2)  # 1 item × 2 pincodes
        
        # Add second item - should create coverage for 2 more pincodes
        pli2 = PriceListItem.objects.create(price_list=pl, item=self.item2)
        count_after_item2 = PriceCoverage.objects.filter(price_list=pl).count()
        self.assertEqual(count_after_item2, 4)  # 2 items × 2 pincodes
        
        # Remove first item - should reduce coverage
        pli1.delete()
        count_after_removal = PriceCoverage.objects.filter(price_list=pl).count()
        self.assertEqual(count_after_removal, 2)  # 1 item × 2 pincodes

    def test_changing_pricelist_dates_updates_coverage_rows(self):
        """Test that changing PriceList dates updates coverage rows"""
        # Create price list with initial dates
        pl = PriceList.objects.create(
            code='PL001', name='Price List 1', territory=self.territory,
            effective_from=date(2024, 1, 1), effective_till=date(2024, 6, 30)
        )
        PriceListItem.objects.create(price_list=pl, item=self.item1)
        
        # Check initial coverage dates
        coverage = PriceCoverage.objects.filter(price_list=pl).first()
        self.assertEqual(coverage.effective_from, date(2024, 1, 1))
        self.assertEqual(coverage.effective_till, date(2024, 6, 30))
        
        # Change price list dates
        pl.effective_from = date(2024, 2, 1)
        pl.effective_till = date(2024, 8, 31)
        pl.save()
        from sales.services import sync_pricelist_coverage
        sync_pricelist_coverage(pl.id)
        # Re-fetch coverage row to ensure latest data
        coverage = PriceCoverage.objects.filter(price_list=pl).first()
        self.assertEqual(coverage.effective_from, date(2024, 2, 1))
        self.assertEqual(coverage.effective_till, date(2024, 8, 31))

    def test_pricelistitem_uses_catalog_item_fk(self):
        """Test that PriceListItem.item correctly references catalog.Item"""
        # Create a catalog Item
        test_item = Item.objects.create(
            name='Test Catalog Item', brand=self.brand,
            category=self.category, tax_rate=self.tax_rate, uom=self.uom, product_type='GOODS', status='ACTIVE'
        )
        
        # Create price list and add the catalog item
        pl = PriceList.objects.create(
            code='PL001', name='Price List 1', territory=self.territory
        )
        pli = PriceListItem.objects.create(price_list=pl, item=test_item)
        
        # Verify the FK relationship works correctly
        self.assertEqual(pli.item, test_item)
        self.assertEqual(pli.item.name, 'Test Catalog Item')
        self.assertEqual(pli.item.brand, self.brand)
        self.assertEqual(pli.item.category, self.category)
        
        # Verify reverse relationship
        price_list_items = test_item.pricelistitem_set.all()
        self.assertIn(pli, price_list_items)
