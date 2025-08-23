from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from geo.models import State, City, Pincode, Territory, TerritoryMember
from sales.models import PriceList, PriceListItem, PriceListTier, PriceListStatus
from catalog.models import Item

class ConflictsAcrossTerritoriesTest(TestCase):
    def setUp(self):
        # Shared geo
        s = State.objects.create(code='DL', name='Delhi', is_active=True)
        c = City.objects.create(state=s, name='New Delhi', is_active=True)
        self.pin = Pincode.objects.create(state=s, city=c, code='110001', is_active=True)
        # Territory T1 (PIN)
        self.t1 = Territory.objects.create(code='T1', name='T1', type='PINCODE')
        TerritoryMember.objects.create(territory=self.t1, pincode=self.pin)
        # Territory T2 (CITY), also covers 110001
        self.t2 = Territory.objects.create(code='T2', name='T2', type='CITY')
        TerritoryMember.objects.create(territory=self.t2, city=c)
        self.item = Item.objects.create(sku='SKU1234567', name='Widget', active=True)

    def test_conflict_block_on_same_item_same_pin(self):
        pl1 = PriceList.objects.create(code='PL-1', name='PL1', territory=self.t1, status=PriceListStatus.DRAFT)
        pli1 = PriceListItem.objects.create(price_list=pl1, item=self.item)
        PriceListTier.objects.create(price_list_item=pli1, max_qty=10, min_unit_price='100.00', is_open_ended=False)

        pl2 = PriceList.objects.create(code='PL-2', name='PL2', territory=self.t2, status=PriceListStatus.DRAFT)
        with self.assertRaises(ValidationError):
            pli2 = PriceListItem(price_list=pl2, item=self.item)
            pli2.full_clean(); pli2.save()

    def test_archiving_first_allows_second(self):
        pl1 = PriceList.objects.create(code='PL-1', name='PL1', territory=self.t1, status=PriceListStatus.DRAFT)
        pli1 = PriceListItem.objects.create(price_list=pl1, item=self.item)
        PriceListTier.objects.create(price_list_item=pli1, max_qty=10, min_unit_price='100.00', is_open_ended=False)
        pl1.status = PriceListStatus.PUBLISHED; pl1.save(update_fields=['status'])

        # Second conflicts now
        pl2 = PriceList.objects.create(code='PL-2', name='PL2', territory=self.t2, status=PriceListStatus.DRAFT)
        with self.assertRaises(ValidationError):
            PriceListItem.objects.create(price_list=pl2, item=self.item)

        # Archive first, then second should pass
        pl1.status = PriceListStatus.ARCHIVED; pl1.save(update_fields=['status'])
        pli2 = PriceListItem(price_list=pl2, item=self.item)
        pli2.full_clean(); pli2.save()

    def test_non_overlapping_dates_allow_both(self):
        today = date.today()
        pl1 = PriceList.objects.create(code='PL-1', name='PL1', territory=self.t1, status=PriceListStatus.DRAFT, effective_from=today, effective_till=today+timedelta(days=10))
        pli1 = PriceListItem.objects.create(price_list=pl1, item=self.item)
        PriceListTier.objects.create(price_list_item=pli1, max_qty=10, min_unit_price='100.00', is_open_ended=False)

        pl2 = PriceList.objects.create(code='PL-2', name='PL2', territory=self.t2, status=PriceListStatus.DRAFT, effective_from=today+timedelta(days=11), effective_till=today+timedelta(days=20))
        pli2 = PriceListItem.objects.create(price_list=pl2, item=self.item)
        pli2.full_clean(); pli2.save()  # no ValidationError expected
