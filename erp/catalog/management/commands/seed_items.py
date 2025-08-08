from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from catalog.models import Brand, Category, UoM, TaxRate, Item

class Command(BaseCommand):
    help = "Seed sample Items for demo/testing"

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()

        # Ensure some lookups exist
        brand, _ = Brand.objects.get_or_create(name="Acme", defaults={"created_by": user, "updated_by": user})
        child = Category.objects.filter(parent__isnull=False).first()
        uom = UoM.objects.filter(active=True).first()
        tax = TaxRate.objects.filter(active=True).first()

        if not (child and uom):
            self.stdout.write(self.style.WARNING("Not enough lookup data to create items (need child category and uom)."))
            return

        Item.objects.get_or_create(
            name="Sample Good",
            defaults={
                "product_type": "GOODS",
                "brand": brand,
                "category": child,
                "uom": uom,
                "tax_rate": tax,
                "status": "ACTIVE",
                "for_sales": True,
                "created_by": user,
                "updated_by": user,
            },
        )
        Item.objects.get_or_create(
            name="Consulting Service",
            defaults={
                "product_type": "SERVICE",
                "brand": brand,
                "category": child,
                "status": "DRAFT",
                "for_sales": True,
                "created_by": user,
                "updated_by": user,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seeded sample items."))
