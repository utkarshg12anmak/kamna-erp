from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum
from django.db import transaction
from django.utils import timezone
from warehousing.models import (
    Warehouse,
    Location,
    StockLedger,
    LocationType,
    VirtualSubtype,
    MovementType,
)

class Command(BaseCommand):
    help = "Zero out RETURN virtual bin for a warehouse by offsetting with LOST bin (per item)."\
        " If RETURN qty > 0 moves to LOST; if < 0 pulls from LOST back to RETURN."\
        " Fails if LOST lacks quantity needed to cover negatives."

    def add_arguments(self, parser):
        parser.add_argument("warehouse_code", help="Warehouse code (e.g. BDVWH)")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done without posting")
        parser.add_argument("--verbose", action="store_true", help="List each item adjustment")
        parser.add_argument("--ref", default=None, help="Custom batch reference (idempotency)")

    def handle(self, warehouse_code, dry_run=False, verbose=False, ref=None, **opts):
        try:
            wh = Warehouse.objects.get(code=warehouse_code)
        except Warehouse.DoesNotExist:
            raise CommandError(f"Warehouse '{warehouse_code}' not found")

        try:
            return_bin = Location.objects.get(warehouse=wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.RETURN)
            lost_bin = Location.objects.get(warehouse=wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.LOST)
        except Location.DoesNotExist:
            raise CommandError("RETURN or LOST virtual bin missing")

        # Aggregate on-hand per item in RETURN & LOST
        return_rows = (StockLedger.objects.filter(warehouse=wh, location=return_bin)
                       .values('item_id').annotate(qty=Sum('qty_delta')))
        lost_rows = (StockLedger.objects.filter(warehouse=wh, location=lost_bin)
                     .values('item_id').annotate(qty=Sum('qty_delta')))
        lost_map = {r['item_id']: r['qty'] or Decimal('0') for r in lost_rows}

        adjustments = []  # (item_id, from_loc, to_loc, qty)
        shortages = []
        for r in return_rows:
            item_id = r['item_id']
            qty = r['qty'] or Decimal('0')
            if qty == 0:
                continue
            if qty > 0:
                # Need to move qty out of RETURN to LOST
                adjustments.append((item_id, return_bin, lost_bin, qty))
            else:  # qty < 0
                need = -qty  # amount to bring RETURN to zero
                lost_available = lost_map.get(item_id, Decimal('0'))
                if lost_available < need:
                    shortages.append((item_id, need, lost_available))
                else:
                    adjustments.append((item_id, lost_bin, return_bin, need))
        if shortages:
            msg_lines = ["Insufficient LOST qty for some items (item, need, available):"]
            for item_id, need, avail in shortages:
                msg_lines.append(f"  {item_id}: need {need} avail {avail}")
            raise CommandError("\n".join(msg_lines))

        if not adjustments:
            self.stdout.write("Nothing to adjust; RETURN already zero per item.")
            return

        total_moves = sum(q for *_ , q in adjustments)
        self.stdout.write(f"Items to adjust: {len(adjustments)}; total absolute qty moved {total_moves}")
        if verbose:
            for item_id, from_loc, to_loc, qty in adjustments:
                self.stdout.write(f"  Item {item_id}: {from_loc.subtype}->{to_loc.subtype} {qty}")

        if dry_run:
            self.stdout.write("Dry run complete. No ledger entries written.")
            return

        batch_ref = ref or f"zero_return:{wh.id}:{timezone.now().isoformat()}"
        if ref and StockLedger.objects.filter(warehouse=wh, ref_model='ZERO_RETURN', ref_id=ref).exists():
            self.stdout.write(self.style.WARNING(f"Batch ref '{ref}' already posted. Aborting."))
            return

        with transaction.atomic():
            for item_id, from_loc, to_loc, qty in adjustments:
                # Out from source
                StockLedger.objects.create(
                    warehouse=wh, location=from_loc, item_id=item_id, qty_delta=-qty,
                    movement_type=MovementType.PUTAWAY_LOST, ref_model='ZERO_RETURN', ref_id=batch_ref,
                    memo='Zero RETURN (out)')
                # In to destination
                StockLedger.objects.create(
                    warehouse=wh, location=to_loc, item_id=item_id, qty_delta=qty,
                    movement_type=MovementType.PUTAWAY_LOST, ref_model='ZERO_RETURN', ref_id=batch_ref,
                    memo='Zero RETURN (in)')
        self.stdout.write(self.style.SUCCESS(f"RETURN bin zeroed. Batch ref: {batch_ref}"))