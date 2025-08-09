from django.core.management.base import BaseCommand
from warehousing.models import Warehouse
from warehousing.services import create_standard_virtual_bins


class Command(BaseCommand):
    help = "Ensure each warehouse has all standard virtual bins."

    def handle(self, *args, **options):
        total_created = 0
        for wh in Warehouse.objects.all():
            created = create_standard_virtual_bins(wh)
            total_created += created
            self.stdout.write(self.style.SUCCESS(f"{wh.code}: created {created} bins"))
        self.stdout.write(self.style.SUCCESS(f"Total created: {total_created}"))
