from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from warehousing.models import Warehouse, StockLedger, MovementType
from django.db.models import Count

class Command(BaseCommand):
    help = "Audit recent PUTAWAY batches (including LOST) and highlight any suspicious duplicate pairs."

    def add_arguments(self, parser):
        parser.add_argument('warehouse', type=str, help='Warehouse code')
        parser.add_argument('--minutes', type=int, default=120, help='Look-back window in minutes (default 120)')
        parser.add_argument('--limit', type=int, default=100, help='Max batches to display')

    def handle(self, *args, **opts):
        code = opts['warehouse']
        minutes = opts['minutes']
        limit = opts['limit']
        wh = Warehouse.objects.get(code=code)
        since = timezone.now() - timedelta(minutes=minutes)
        qs = StockLedger.objects.filter(warehouse=wh, ref_model='PUTAWAY', ts__gte=since)
        batches = (
            qs.values('ref_id')
              .annotate(rows=Count('id'))
              .order_by('-rows','ref_id')[:limit]
        )
        if not batches:
            self.stdout.write(self.style.WARNING('No batches in window.'))
            return
        self.stdout.write(f"Batches in last {minutes} min (limit {limit}):")
        for b in batches:
            ref = b['ref_id']
            rows = b['rows']
            lost_rows = qs.filter(ref_id=ref, movement_type=MovementType.PUTAWAY_LOST).count()
            put_rows = qs.filter(ref_id=ref, movement_type=MovementType.PUTAWAY).count()
            pairs = rows//2
            status = ''
            # Each logical action group should produce exactly 2 ledger rows. If odd rows -> anomaly.
            if rows % 2 != 0:
                status += 'ODD_ROWS ' 
            if lost_rows not in (0,2,4,6,8):  # heuristic: lost rows should be even and usually small
                status += 'LOST_ODD ' 
            self.stdout.write(f"- {ref}: total_rows={rows} pairs~={pairs} put_rows={put_rows} lost_rows={lost_rows} {status}")
        # Highlight any duplicate logical groups (same item/location/qty/movement_type recorded twice under different ref_ids)
        # This helps spot rapid duplicate LOST postings with differing random id keys.
        dup_probe = (
            qs.values('movement_type','location_id','item_id')
              .annotate(n=Count('id'))
              .filter(n__gt=4)  # more than 2 pairs
        )
        if dup_probe:
            self.stdout.write(self.style.WARNING('Potential duplicates (high row counts per movement/location/item across batches):'))
            for d in dup_probe:
                self.stdout.write(f"  movement={d['movement_type']} location={d['location_id']} item={d['item_id']} rows={d['n']}")
        else:
            self.stdout.write('No high-count duplicate patterns detected.')
