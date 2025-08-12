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
from warehousing.services import post_ledger
from catalog.models import Item


class Command(BaseCommand):
    help = "Clear ALL stock in a warehouse to zero by posting balancing entries to null (complete inventory reset)."

    def add_arguments(self, parser):
        parser.add_argument("warehouse_code", help="Warehouse code (e.g. BDVWH)")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done without posting")
        parser.add_argument("--verbose", action="store_true", help="List each item adjustment")
        parser.add_argument("--ref", default=None, help="Custom batch reference (idempotency)")
        parser.add_argument(
            "--include-physical", 
            action="store_true", 
            help="Also clear physical location stock (default: only virtual bins)"
        )
        parser.add_argument(
            "--bins",
            default="RETURN,RECEIVE,DAMAGE,LOST",
            help="Comma-separated virtual subtypes to clear (default: RETURN,RECEIVE,DAMAGE,LOST)"
        )

    def handle(self, warehouse_code, dry_run=False, verbose=False, ref=None, include_physical=False, bins=None, **opts):
        try:
            wh = Warehouse.objects.get(code=warehouse_code)
        except Warehouse.DoesNotExist:
            raise CommandError(f"Warehouse '{warehouse_code}' not found")

        self.stdout.write(f"Warehouse: {wh.code} - {wh.name}")
        
        # Parse bins
        virtual_bins = [b.strip().upper() for b in (bins or "").split(",") if b.strip()]
        if not virtual_bins:
            virtual_bins = ["RETURN", "RECEIVE", "DAMAGE", "LOST"]

        # Validate virtual subtypes
        valid_subtypes = dict(VirtualSubtype.choices)
        for bin_name in virtual_bins:
            if bin_name not in valid_subtypes:
                raise CommandError(f"Invalid virtual bin: {bin_name}")

        batch_ref = ref or f"clear_warehouse:{wh.id}:{timezone.now().isoformat()}"
        if ref and StockLedger.objects.filter(warehouse=wh, ref_model='CLEAR_WAREHOUSE', ref_id=ref).exists():
            self.stdout.write(self.style.WARNING(f"Batch ref '{ref}' already posted. Aborting."))
            return

        total_adjustments = 0

        # Process virtual bins
        self.stdout.write(f"\n=== VIRTUAL BINS ({', '.join(virtual_bins)}) ===")
        for bin_name in virtual_bins:
            try:
                vb = Location.objects.get(
                    warehouse=wh, 
                    type=LocationType.VIRTUAL, 
                    subtype=bin_name
                )
            except Location.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  {bin_name}: Virtual bin not found, skipping"))
                continue

            # Aggregate on-hand per item
            agg = (
                StockLedger.objects.filter(warehouse=wh, location=vb)
                .values("item_id")
                .annotate(qty=Sum("qty_delta"))
                .order_by("item_id")
            )
            rows = [r for r in agg if (r.get("qty") or Decimal("0")) != 0]
            
            if not rows:
                self.stdout.write(f"  {bin_name}: Already zero")
                continue

            self.stdout.write(f"  {bin_name}: Found {len(rows)} item(s) with stock")
            
            for r in rows:
                item_id = r["item_id"]
                qty = Decimal(r.get("qty") or 0)
                
                try:
                    item = Item.objects.get(id=item_id)
                except Item.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"    Skipping missing item {item_id}"))
                    continue

                direction = "OUT" if qty > 0 else "IN"
                abs_qty = abs(qty)
                
                if verbose:
                    self.stdout.write(f"    {item.sku}: {direction} {abs_qty} (current: {qty})")
                
                if dry_run:
                    continue

                with transaction.atomic():
                    if qty > 0:
                        # Post out to null
                        post_ledger(
                            warehouse=wh,
                            from_location=vb,
                            to_location=None,
                            item=item,
                            qty=abs_qty,
                            movement_type=MovementType.TRANSFER,
                            user=None,
                            ref_model="CLEAR_WAREHOUSE",
                            ref_id=batch_ref,
                            memo=f"Clear {bin_name} to zero (OUT)",
                        )
                    else:
                        # Post in from null
                        post_ledger(
                            warehouse=wh,
                            from_location=None,
                            to_location=vb,
                            item=item,
                            qty=abs_qty,
                            movement_type=MovementType.TRANSFER,
                            user=None,
                            ref_model="CLEAR_WAREHOUSE",
                            ref_id=batch_ref,
                            memo=f"Clear {bin_name} to zero (IN)",
                        )
                    total_adjustments += 1

        # Process physical locations if requested
        if include_physical:
            self.stdout.write(f"\n=== PHYSICAL LOCATIONS ===")
            
            physical_locations = Location.objects.filter(
                warehouse=wh,
                type=LocationType.PHYSICAL
            ).order_by('code')
            
            for loc in physical_locations:
                # Aggregate on-hand per item in this physical location
                agg = (
                    StockLedger.objects.filter(warehouse=wh, location=loc)
                    .values("item_id")
                    .annotate(qty=Sum("qty_delta"))
                    .order_by("item_id")
                )
                rows = [r for r in agg if (r.get("qty") or Decimal("0")) != 0]
                
                if not rows:
                    continue
                
                loc_name = loc.display_name or loc.code
                self.stdout.write(f"  {loc_name}: Found {len(rows)} item(s) with stock")
                
                for r in rows:
                    item_id = r["item_id"]
                    qty = Decimal(r.get("qty") or 0)
                    
                    try:
                        item = Item.objects.get(id=item_id)
                    except Item.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"    Skipping missing item {item_id}"))
                        continue

                    direction = "OUT" if qty > 0 else "IN"
                    abs_qty = abs(qty)
                    
                    if verbose:
                        self.stdout.write(f"    {item.sku}: {direction} {abs_qty} (current: {qty})")
                    
                    if dry_run:
                        continue

                    with transaction.atomic():
                        if qty > 0:
                            # Post out to null
                            post_ledger(
                                warehouse=wh,
                                from_location=loc,
                                to_location=None,
                                item=item,
                                qty=abs_qty,
                                movement_type=MovementType.TRANSFER,
                                user=None,
                                ref_model="CLEAR_WAREHOUSE",
                                ref_id=batch_ref,
                                memo=f"Clear {loc_name} to zero (OUT)",
                            )
                        else:
                            # Post in from null
                            post_ledger(
                                warehouse=wh,
                                from_location=None,
                                to_location=loc,
                                item=item,
                                qty=abs_qty,
                                movement_type=MovementType.TRANSFER,
                                user=None,
                                ref_model="CLEAR_WAREHOUSE",
                                ref_id=batch_ref,
                                memo=f"Clear {loc_name} to zero (IN)",
                            )
                        total_adjustments += 1

        if dry_run:
            self.stdout.write(self.style.NOTICE(f"\nDry run complete. Would post {total_adjustments} adjustments."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nDone! Posted {total_adjustments} adjustments. Batch ref: {batch_ref}"))
