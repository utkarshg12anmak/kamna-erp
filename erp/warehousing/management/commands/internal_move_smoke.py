from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from warehousing.models import Warehouse, Location, LocationType
from warehousing.services_internal_move import InternalMoveLine, post_internal_move


class Command(BaseCommand):
    help = "Smoke test for internal movement: moves 1 unit between two physical locations with available stock"

    def add_arguments(self, parser):
        parser.add_argument("warehouse", type=str, help="Warehouse code")
        parser.add_argument("item", type=int, help="Item ID")
        parser.add_argument("source", type=int, help="Source location ID")
        parser.add_argument("target", type=int, help="Target location ID")
        parser.add_argument("--user", type=str, default=None, help="Username to attribute the move")
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **opts):
        code = opts["warehouse"]
        item_id = int(opts["item"])
        src = int(opts["source"])
        dst = int(opts["target"])
        dry = bool(opts["dry-run"]) 

        wh = Warehouse.objects.get(code=code)
        for loc_id in [src, dst]:
            loc = Location.objects.get(id=loc_id)
            if loc.warehouse_id != wh.id:
                self.stderr.write(self.style.ERROR("Locations must belong to the given warehouse"))
                return
            if loc.type != LocationType.PHYSICAL:
                self.stderr.write(self.style.ERROR("Locations must be PHYSICAL"))
                return
        username = opts.get("user")
        User = get_user_model()
        user = User.objects.filter(username=username).first() if username else User.objects.first()
        if not user:
            self.stderr.write(self.style.ERROR("No user available to attribute the move"))
            return
        line = InternalMoveLine(item_id=item_id, source_location_id=src, target_location_id=dst, qty=Decimal("1"))
        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN — would post an internal movement."))
            return
        result = post_internal_move(user, [line], batch_ref_id=None)
        self.stdout.write(self.style.SUCCESS(f"OK — posted {result.get('posted')} entries."))
