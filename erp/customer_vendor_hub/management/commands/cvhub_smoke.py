from django.core.management.base import BaseCommand, CommandError
from customer_vendor_hub.models import Partner


class Command(BaseCommand):
    help = "Smoke test for Customer & Vendor Hub"

    def handle(self, *args, **options):
        count = Partner.objects.count()
        if count == 0:
            raise CommandError("No partners found. Run cvhub_seed first.")
        self.stdout.write(self.style.SUCCESS(f"CVHub OK. Partners: {count}"))
