from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from decimal import Decimal
from warehousing.models import Warehouse, Location, LocationType, WarehouseStatus, StockLedger, MovementType
from warehousing.services_internal_move import post_internal_move_rows
from catalog.models import Item

class Command(BaseCommand):
    help = "Smoke test for row-form Internal Movement"

    def handle(self, *args, **opts):
        # Preconditions: pick first warehouse or create
        wh = Warehouse.objects.first()
        if not wh:
            raise CommandError('No warehouse found')
        # Ensure at least two PHYSICAL ACTIVE locations
        phys = list(Location.objects.filter(warehouse=wh, type=LocationType.PHYSICAL, status=WarehouseStatus.ACTIVE)[:2])
        if len(phys) < 2:
            raise CommandError('Need at least two PHYSICAL ACTIVE locations')
        src, dst = phys[0], phys[1]
        # Ensure two catalog items
        it = Item.objects.first()
        if not it:
            raise CommandError('No items found')
        items = [it]
        if Item.objects.count() == 1:
            # create one
            items.append(Item.objects.create(name='IM Smoke', product_type='GOODS'))
        else:
            items.append(Item.objects.exclude(id=it.id).first())
        # Seed stock at source
        for i, qty in zip(items, (Decimal('7'), Decimal('5'))):
            StockLedger.objects.create(warehouse=wh, location=src, item=i, qty_delta=qty, movement_type=MovementType.TRANSFER, ref_model='SMOKE')
        # User
        User = get_user_model()
        user = User.objects.first()
        if not user:
            raise CommandError('No user to attribute move')
        # Execute move
        lines = [{ 'item': items[0].id, 'qty': Decimal('3') }, { 'item': items[1].id, 'qty': Decimal('2') }]
        res = post_internal_move_rows(wh, src.id, dst.id, lines, user, memo='rows smoke')
        if not res.get('ok'):
            raise CommandError(f"Unexpected failure: {res}")
        # Validate postings
        outs = StockLedger.objects.filter(warehouse=wh, location=src, movement_type=MovementType.INTERNAL_TRANSFER).order_by('-id')[:2]
        ins = StockLedger.objects.filter(warehouse=wh, location=dst, movement_type=MovementType.INTERNAL_TRANSFER).order_by('-id')[:2]
        if sum((-o.qty_delta) for o in outs) != Decimal('5'):
            raise CommandError('Source totals mismatch')
        if sum(i.qty_delta for i in ins) != Decimal('5'):
            raise CommandError('Target totals mismatch')
        # Over-request test
        res2 = post_internal_move_rows(wh, src.id, dst.id, [{ 'item': items[0].id, 'qty': Decimal('9999') }], user)
        if res2.get('ok') or str(items[0].id) not in (res2.get('errors') or {}):
            raise CommandError('Expected error for over-request not present')
        self.stdout.write(self.style.SUCCESS('INTERNAL_MOVE_ROWS_SMOKE_OK'))
