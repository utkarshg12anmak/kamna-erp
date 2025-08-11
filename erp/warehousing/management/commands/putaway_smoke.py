from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from warehousing.models import Warehouse, Location, LocationType, VirtualSubtype, StockLedger, MovementType
from catalog.models import Item, Brand, Category, UoM, TaxRate
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds minimal data and exercises putaway KPIs/list/confirm APIs via direct service calls."

    def add_arguments(self, parser):
        parser.add_argument('--warehouse', type=str, help='Warehouse code to use or create', default='PUTAW')
        parser.add_argument('--dry-run', action='store_true')

    @transaction.atomic
    def handle(self, *args, **opts):
        code = opts['warehouse']
        dry = opts['dry_run']
        # Ensure user
        user, _ = User.objects.get_or_create(username='putaway_tester', defaults={'is_staff': True})
        # Ensure catalog basics
        brand, _ = Brand.objects.get_or_create(name='BrandX')
        root_cat, _ = Category.objects.get_or_create(name='RootX', parent=None)
        child_cat, _ = Category.objects.get_or_create(name='ChildX', parent=root_cat)
        uom, _ = UoM.objects.get_or_create(code='EA', defaults={'name':'Each','ratio_to_base':1,'base':True})
        tax, _ = TaxRate.objects.get_or_create(name='GST0', defaults={'percent':0})
        item, _ = Item.objects.get_or_create(name='Putaway Sample', defaults={
            'product_type':'GOODS', 'brand':brand, 'category':child_cat, 'uom':uom, 'tax_rate':tax, 'status':'ACTIVE'
        })
        # Ensure warehouse with virtuals exists (signals create bins)
        wh, _ = Warehouse.objects.get_or_create(code=code, defaults={
            'name':'Putaway WH','status':'ACTIVE','gstin':'27ABCDE1234F1Z5','address_line1':'','address_line2':'',
            'city':'City','state':'State','pincode':'123456','country':'India','latitude':0,'longitude':0
        })
        # Ensure a physical location
        ploc, _ = Location.objects.get_or_create(warehouse=wh, type=LocationType.PHYSICAL, code='A1', defaults={
            'display_name':'Aisle A1'
        })
        # Virtual bins
        rbin = Location.objects.get(warehouse=wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.RETURN)
        recv = Location.objects.get(warehouse=wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.RECEIVE)
        # Seed stock into RETURN and RECEIVE
        StockLedger.objects.create(warehouse=wh, location=rbin, item=item, qty_delta=Decimal('5'), movement_type=MovementType.TRANSFER, ref_model='SEED', memo='seed return')
        StockLedger.objects.create(warehouse=wh, location=recv, item=item, qty_delta=Decimal('7'), movement_type=MovementType.TRANSFER, ref_model='SEED', memo='seed receive')
        self.stdout.write(self.style.SUCCESS('Seeded stock: RETURN +5, RECEIVE +7'))
        if dry:
            self.stdout.write(self.style.WARNING('Dry run complete.'))
            return
        # Do a putaway batch: move 3 from RETURN to A1, mark 2 from RECEIVE as LOST
        from warehousing.services_putaway import post_actions
        result = post_actions(wh, [
            {'type':'PUTAWAY','item':item.id,'source_bin':rbin.id,'qty':Decimal('3'),'target_location':ploc.id},
            {'type':'LOST','item':item.id,'source_bin':recv.id,'qty':Decimal('2')},
        ], user=user, reason_map={'RETURN':'return putaway','RECEIVE':'receive putaway'})
        self.stdout.write(self.style.SUCCESS(f"Posted actions: {result}"))
        # Validate balances
        def bal(loc):
            from django.db.models import Sum
            return (StockLedger.objects.filter(warehouse=wh, location=loc, item=item).aggregate(Sum('qty_delta'))['qty_delta__sum'] or Decimal('0'))
        self.stdout.write(f"RETURN bal: {bal(rbin)}; RECEIVE bal: {bal(recv)}; A1 bal: {bal(ploc)}")
        self.stdout.write(self.style.SUCCESS('Putaway smoke complete.'))
