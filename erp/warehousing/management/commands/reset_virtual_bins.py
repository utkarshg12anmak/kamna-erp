# filepath: /Users/dealshare/Documents/GitHub/kamna-erp/erp/warehousing/management/commands/reset_virtual_bins.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

from warehousing.models import Warehouse, StockLedger, MovementType, LocationType, VirtualSubtype
from warehousing.services import get_virtual, post_ledger
from catalog.models import Item


class Command(BaseCommand):
    help = (
        "Reset specified virtual bins to zero by posting balancing ledger entries per item. "
        "Defaults to RETURN and LOST."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--warehouse",
            dest="warehouse",
            help="Warehouse code or id. If omitted, all warehouses are processed.",
        )
        parser.add_argument(
            "--bins",
            dest="bins",
            default="RETURN,LOST",
            help="Comma-separated virtual subtypes to reset (e.g., RETURN,LOST).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print actions without posting.",
        )

    def _get_warehouse(self, ident: str | None):
        if not ident:
            return None
        try:
            return Warehouse.objects.get(id=int(ident))
        except Exception:
            try:
                return Warehouse.objects.get(code=ident)
            except Warehouse.DoesNotExist:
                raise CommandError(f"Warehouse '{ident}' not found")

    def handle(self, *args, **options):
        wh_filter = self._get_warehouse(options.get("warehouse"))
        bins_arg = options.get("bins") or "RETURN,LOST"
        dry_run = options.get("dry_run")

        # Validate subtypes
        subtype_map = {s: s for s, _ in VirtualSubtype.choices}
        target_subtypes = []
        for part in [p.strip().upper() for p in bins_arg.split(",") if p.strip()]:
            if part not in subtype_map:
                raise CommandError(f"Invalid virtual subtype: {part}")
            target_subtypes.append(part)
        if not target_subtypes:
            self.stdout.write("No subtypes provided; nothing to do.")
            return

        warehouses = [wh_filter] if wh_filter else list(Warehouse.objects.all().order_by("code"))
        total_adjustments = 0

        for wh in warehouses:
            self.stdout.write(self.style.NOTICE(f"[{wh.code}] Processing subtypes: {', '.join(target_subtypes)}"))
            for st in target_subtypes:
                try:
                    vb = get_virtual(wh, st)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  - {st}: {e}"))
                    continue
                if vb.type != LocationType.VIRTUAL:
                    self.stdout.write(self.style.WARNING(f"  - {st}: Not a virtual location; skipping"))
                    continue

                # Aggregate on-hand per item at this bin
                agg = (
                    StockLedger.objects.filter(warehouse=wh, location=vb)
                    .values("item_id")
                    .annotate(q=Sum("qty_delta"))
                    .order_by("item_id")
                )
                rows = [r for r in agg if (r.get("q") or Decimal("0")) != 0]
                if not rows:
                    self.stdout.write(self.style.SUCCESS(f"  - {st}: Already zero"))
                    continue

                self.stdout.write(f"  - {st}: Found {len(rows)} item balance(s) to clear")

                for r in rows:
                    item_id = r.get("item_id")
                    if item_id is None:
                        continue
                    qty = Decimal(r.get("q") or 0)
                    item = Item.objects.get(id=int(item_id))

                    if dry_run:
                        if qty > 0:
                            self.stdout.write(f"      • OUT {qty} of {item.sku} from {st} -> null")
                        else:
                            self.stdout.write(f"      • IN {abs(qty)} of {item.sku} from null -> {st}")
                        continue

                    with transaction.atomic():
                        if qty > 0:
                            # Post out to null to bring balance to zero
                            post_ledger(
                                warehouse=wh,
                                from_location=vb,
                                to_location=None,
                                item=item,
                                qty=qty,
                                movement_type=MovementType.TRANSFER,
                                user=None,
                                ref_model="maintenance.ResetBins",
                                ref_id=f"reset-{st}-{timezone.now().isoformat()}",
                                memo=f"Reset {st} to zero (OUT)",
                            )
                        else:
                            # Post in from null to bring negative balance up to zero
                            post_ledger(
                                warehouse=wh,
                                from_location=None,
                                to_location=vb,
                                item=item,
                                qty=abs(qty),
                                movement_type=MovementType.TRANSFER,
                                user=None,
                                ref_model="maintenance.ResetBins",
                                ref_id=f"reset-{st}-{timezone.now().isoformat()}",
                                memo=f"Reset {st} to zero (IN)",
                            )
                        total_adjustments += 1

                self.stdout.write(self.style.SUCCESS(f"  - {st}: Cleared {len(rows)} item balance(s)"))

        self.stdout.write(self.style.SUCCESS(f"Done. Warehouses: {len(warehouses)}. Adjustments posted: {total_adjustments}."))
