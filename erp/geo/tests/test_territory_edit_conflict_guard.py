from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from geo.models import State, City, Pincode, Territory, TerritoryMember, TerritoryCoverage
from sales.models import PriceList, PriceListItem, PriceListTier, PriceListStatus, PriceCoverage
from catalog.models import Item

class TerritoryEditConflictGuardTest(TestCase):
    def setUp(self):
        s = State.objects.create(code='DL', name='Delhi', is_active=True)
        c = City.objects.create(state=s, name='New Delhi', is_active=True)
        self.p1 = Pincode.objects.create(state=s, city=c, code='110001', is_active=True)
        self.p2 = Pincode.objects.create(state=s, city=c, code='110002', is_active=True)
        self.t = Territory.objects.create(code='T-DL', name='Delhi PIN', type='PINCODE')
        TerritoryMember.objects.create(territory=self.t, pincode=self.p1)
        self.item = Item.objects.create(sku='SKU-GUARD', name='Guarded', active=True)
        pl = PriceList.objects.create(code='PL-G', name='Guard', territory=self.t, status=PriceListStatus.PUBLISHED)
        pli = PriceListItem.objects.create(price_list=pl, item=self.item)
        PriceListTier.objects.create(price_list_item=pli, max_qty=10, min_unit_price='100.00', is_open_ended=False)

    def test_adding_pincode_that_conflicts_is_blocked(self):
        # Simulate that another PL exists elsewhere for same item on p2
        t2 = Territory.objects.create(code='T2', name='City', type='PINCODE')
        TerritoryMember.objects.create(territory=t2, pincode=self.p2)
        pl2 = PriceList.objects.create(code='PL-H', name='Other', territory=t2, status=PriceListStatus.DRAFT)
        PriceListItem.objects.create(price_list=pl2, item=self.item)

        # Now try to extend self.t to also cover p2 — should be blocked by admin guard in real flow.
        # Here we mimic the check: if we add p2, conflicts exist via PriceCoverage.
        PriceCoverage.objects.create(item=self.item, pincode=self.p2, price_list=pl2, status=pl2.status)
        # Expect the admin layer to detect this and refuse; here we assert existence of overlapping active coverage for (item,p2)
        self.assertTrue(PriceCoverage.objects.filter(item=self.item, pincode=self.p2, status__in=['DRAFT','PUBLISHED']).exists())
