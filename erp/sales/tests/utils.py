from geo.models import State, City, Pincode, Territory, TerritoryMember
from catalog.models import Item
from sales.models import PriceList, PriceListItem, PriceListTier, PriceListStatus

def make_geo_simple(state_code='DL', city_name='New Delhi', pincode='110001'):
    s = State.objects.create(code=state_code, name=state_code, is_active=True)
    c = City.objects.create(state=s, name=city_name, is_active=True)
    p = Pincode.objects.create(state=s, city=c, code=pincode, is_active=True)
    t = Territory.objects.create(code=f'{state_code}-T1', name='Test Territory', type='PINCODE')
    TerritoryMember.objects.create(territory=t, pincode=p)
    return s, c, p, t

def make_item(sku='SKU0000001', name='Test Item'):
    return Item.objects.create(sku=sku, name=name, active=True)

def make_pricelist(territory, code='PL-TEST', status=PriceListStatus.DRAFT, ef=None, et=None):
    return PriceList.objects.create(code=code, name=code, territory=territory, status=status, effective_from=ef, effective_till=et)

def add_item_with_tiers(pl, item, tiers):
    """tiers: list of dicts like [{'max_qty':10,'min_unit_price':'100.00','is_open_ended':False}, {'max_qty':None,'min_unit_price':'90.00','is_open_ended':True}]"""
    pli = PriceListItem.objects.create(price_list=pl, item=item)
    for t in tiers:
        PriceListTier.objects.create(price_list_item=pli, **t)
    return pli
