from django.core.management.base import BaseCommand
from customer_vendor_hub.models import State, City, Partner, GSTRegistration, Address


class Command(BaseCommand):
    help = "Seed initial data for Customer & Vendor Hub"

    def handle(self, *args, **options):
        # Basic states and cities (minimal)
        ka, _ = State.objects.get_or_create(code="KA", defaults={"name": "Karnataka"})
        mh, _ = State.objects.get_or_create(code="MH", defaults={"name": "Maharashtra"})
        blr, _ = City.objects.get_or_create(name="Bengaluru", state=ka)
        mum, _ = City.objects.get_or_create(name="Mumbai", state=mh)

        # Demo partners
        acme, _ = Partner.objects.get_or_create(name="ACME Supplies", defaults={"is_vendor": True})
        beta, _ = Partner.objects.get_or_create(name="Beta Retail", defaults={"is_customer": True})

        GSTRegistration.objects.get_or_create(partner=acme, gstin="29ABCDE1234F1Z5", defaults={"legal_name": "ACME Supplies Pvt Ltd", "is_default": True})
        GSTRegistration.objects.get_or_create(partner=beta, gstin="27ABCDE1234F1Z5", defaults={"legal_name": "Beta Retail Ltd", "is_default": True})

        Address.objects.get_or_create(partner=acme, type="SHIPPING", line1="Industrial Area", city=blr, postal_code="560001", defaults={"is_primary": True})
        Address.objects.get_or_create(partner=beta, type="SHIPPING", line1="Main Street", city=mum, postal_code="400001", defaults={"is_primary": True})

        self.stdout.write(self.style.SUCCESS("Seeded Customer & Vendor Hub demo data."))
