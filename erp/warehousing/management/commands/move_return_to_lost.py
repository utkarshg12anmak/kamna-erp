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
    help = "Move all on-hand stock (per item) from RETURN virtual bin to LOST virtual bin for a warehouse."

    def add_arguments(self, parser):
        parser.add_argument("warehouse_code", help="Warehouse code (e.g. BDVWH)")
        parser.add_argument("--dry-run", action="store_true", help="Show what would move, do not post")
        parser.add_argument("--verbose", action="store_true", help="List each item and qty")
        parser.add_argument("--ref", default=None, help="Custom batch reference (idempotency)")

    def handle(self, warehouse_code, dry_run=False, verbose=False, ref=None, **opts):
        try:
            wh = Warehouse.objects.get(code=warehouse_code)
        except Warehouse.DoesNotExist:
            raise CommandError(f"Warehouse '{warehouse_code}' not found")

        try:
            return_bin = Location.objects.get(
                warehouse=wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.RETURN
            )
            lost_bin = Location.objects.get(
                warehouse=wh, type=LocationType.VIRTUAL, subtype=VirtualSubtype.LOST
            )
        except Location.DoesNotExist:
            raise CommandError("RETURN or LOST virtual bin missing in this warehouse")

        rows = (
            StockLedger.objects.filter(warehouse=wh, location=return_bin)
            .values("item_id")
            .annotate(qty=Sum("qty_delta"))
        )

        moves = [(r["item_id"], r["qty"]) for r in rows if (r["qty"] or 0) > 0]
        total_qty = sum((q for _, q in moves), Decimal("0"))
        self.stdout.write(
            f"Warehouse {wh.code} RETURN → LOST candidate items: {len(moves)}, total qty {total_qty}"
        )
        if verbose:
            for item_id, qty in moves:
                self.stdout.write(f"  Item {item_id}: {qty}")

        if dry_run:
            self.stdout.write("Dry run complete. No ledger entries written.")
            return

        if not moves:
            self.stdout.write("Nothing to move.")
            return

        batch_ref = ref or f"return_to_lost:{wh.id}:{timezone.now().isoformat()}"
        if ref and StockLedger.objects.filter(warehouse=wh, ref_model="RETURN_TO_LOST", ref_id=ref).exists():
            self.stdout.write(self.style.WARNING(f"Batch ref '{ref}' already posted. Aborting."))
            return

        with transaction.atomic():
            for item_id, qty in moves:
                StockLedger.objects.create(
                    warehouse=wh,
                    location=return_bin,
                    item_id=item_id,
                    qty_delta=-qty,
                    movement_type=MovementType.PUTAWAY_LOST,
                    ref_model="RETURN_TO_LOST",
                    ref_id=batch_ref,
                    memo="Return→Lost consolidation",
                )
                StockLedger.objects.create(
                    warehouse=wh,
                    location=lost_bin,
                    item_id=item_id,
                    qty_delta=qty,
                    movement_type=MovementType.PUTAWAY_LOST,
                    ref_model="RETURN_TO_LOST",
                    ref_id=batch_ref,
                    memo="Return→Lost consolidation",
                )

        self.stdout.write(self.style.SUCCESS("Return bin emptied into Lost bin."))
        self.stdout.write(f"Batch ref: {batch_ref}")