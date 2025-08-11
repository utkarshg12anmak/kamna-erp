from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum

from warehousing.models import Warehouse, StockLedger, MovementType, LocationType, VirtualSubtype
from warehousing.services import get_virtual, post_ledger
from catalog.models import Item


class Command(BaseCommand):
    help = "Fix stuck quantities in EXCESS_PENDING virtual bin by posting out to null (decline-style)."

    def add_arguments(self, parser):
        parser.add_argument("--warehouse", dest="warehouse", help="Warehouse code or id to fix; if omitted, all warehouses are scanned.")
        parser.add_argument("--dry-run", action="store_true", help="Only show what will be changed without posting.")
        parser.add_argument("--limit", type=int, default=0, help="Optional limit for number of item rows to process per warehouse.")

    def _get_warehouse(self, ident: str | None):
        if not ident:
            return None
        # Try by id then by code
        try:
            return Warehouse.objects.get(id=int(ident))
        except Exception:
            try:
                return Warehouse.objects.get(code=ident)
            except Warehouse.DoesNotExist:
                raise CommandError(f"Warehouse '{ident}' not found")

    def handle(self, *args, **options):
        wh_filter = self._get_warehouse(options.get("warehouse"))
        dry_run = options.get("dry_run")
        limit = options.get("limit") or 0

        warehouses = [wh_filter] if wh_filter else list(Warehouse.objects.all().order_by("code"))
        total_fixed = 0
        for wh in warehouses:
            try:
                vb = get_virtual(wh, VirtualSubtype.EXCESS_PENDING)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"[{wh.code}] No EXCESS_PENDING bin: {e}"))
                continue

            # Aggregate pending qty per item
            agg = (
                StockLedger.objects.filter(warehouse=wh, location=vb)
                .values("item_id")
                .order_by("item_id")
                .annotate(qty=Sum("qty_delta"))
            )
            rows = [r for r in agg if (r.get("qty") or Decimal("0")) > 0]
            if not rows:
                self.stdout.write(self.style.SUCCESS(f"[{wh.code}] No stuck qty in EXCESS_PENDING"))
                continue

            if limit:
                rows = rows[:limit]

            self.stdout.write(f"[{wh.code}] Found {len(rows)} item(s) with pending qty in EXCESS_PENDING")
            for r in rows:
                item_id = int(r["item_id"]) if r["item_id"] is not None else None
                qty = Decimal(r.get("qty") or 0)
                if not item_id:
                    continue
                item = Item.objects.get(id=item_id)
                if dry_run:
                    self.stdout.write(f"  - Would post out {qty} of {item.sku} from EXCESS_PENDING -> null")
                    continue
                with transaction.atomic():
                    post_ledger(
                        warehouse=wh,
                        from_location=vb,
                        to_location=None,
                        item=item,
                        qty=qty,
                        movement_type=MovementType.ADJ_DECLINE_EXCESS,
                        user=None,
                        ref_model="maintenance.DataFix",
                        ref_id=f"fix-excess-{timezone.now().isoformat()}",
                        memo="Cleanup: move pending EXCESS to null",
                    )
                    total_fixed += 1
            self.stdout.write(self.style.SUCCESS(f"[{wh.code}] Completed. Processed {len(rows)} rows."))

        self.stdout.write(self.style.SUCCESS(f"Done. Warehouses processed: {len(warehouses)}. Rows posted: {total_fixed}."))
