from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum
from warehousing.models import Warehouse, VirtualSubtype, StockLedger, MovementType
from warehousing.services import get_virtual, post_ledger
from catalog.models import Item


class Command(BaseCommand):
    help = "Zero out RETURN and LOST virtual bins by posting balancing entries (data fix)."

    def add_arguments(self, parser):
        parser.add_argument("--warehouse", required=True, help="Warehouse code or ID")
        parser.add_argument("--dry-run", action="store_true", help="Do not post, just show what would change")
        parser.add_argument(
            "--bins",
            nargs="*",
            choices=[VirtualSubtype.RETURN, VirtualSubtype.LOST],
            default=[VirtualSubtype.RETURN, VirtualSubtype.LOST],
            help="Which virtual bins to clear (default: RETURN LOST)",
        )

    def handle(self, *args, **options):
        wh_arg = options["warehouse"]
        dry = options["dry_run"]
        bin_list = options["bins"]

        # Resolve warehouse
        try:
            wh = Warehouse.objects.get(code=wh_arg)
        except Warehouse.DoesNotExist:
            try:
                wh = Warehouse.objects.get(pk=int(wh_arg))
            except Exception as e:
                raise CommandError(f"Warehouse not found: {wh_arg}") from e

        self.stdout.write(self.style.NOTICE(f"Clearing bins for warehouse {wh.code} ({wh.id}) -> {', '.join(bin_list)}"))

        total_posts = 0
        for subtype in bin_list:
            loc = get_virtual(wh, subtype)
            per_item = (
                StockLedger.objects.filter(warehouse=wh, location=loc)
                .values("item_id")
                .annotate(q=Sum("qty_delta"))
            )
            to_post = [(int(r["item_id"]), Decimal(r.get("q") or 0)) for r in per_item if (r.get("q") or 0) != 0]
            if not to_post:
                self.stdout.write(self.style.SUCCESS(f"{subtype}: already 0"))
                continue

            for item_id, net in to_post:
                qty = abs(net)
                direction = "OUT" if net > 0 else "IN"
                msg = f"{subtype}: item {item_id} net={net} => post {direction} qty {qty}"
                if dry:
                    self.stdout.write("DRY-RUN " + msg)
                    continue
                # Get item instance
                try:
                    item = Item.objects.get(pk=item_id)
                except Item.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Skipping missing item {item_id}"))
                    continue
                # Post balancing entry; reuse ADJ_DECLINE_EXCESS as a write-off/write-on movement to null
                if net > 0:
                    # remove stock (from bin to null)
                    post_ledger(
                        warehouse=wh,
                        from_location=loc,
                        to_location=None,
                        item=item,
                        qty=qty,
                        movement_type=MovementType.ADJ_DECLINE_EXCESS,
                        user=None,
                        ref_model="datafix",
                        ref_id=f"clear:{subtype}",
                        memo=f"data-fix clear {subtype}",
                    )
                else:
                    # add stock (from null to bin)
                    post_ledger(
                        warehouse=wh,
                        from_location=None,
                        to_location=loc,
                        item=item,
                        qty=qty,
                        movement_type=MovementType.ADJ_DECLINE_EXCESS,
                        user=None,
                        ref_model="datafix",
                        ref_id=f"clear:{subtype}",
                        memo=f"data-fix clear {subtype}",
                    )
                total_posts += 1
                self.stdout.write(self.style.WARNING(msg))

        if dry:
            self.stdout.write(self.style.NOTICE("Dry run complete (no changes)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Done. Posted {total_posts} balancing entries."))
