from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from catalog.models import Category, TaxRate, UoM
from decimal import Decimal

class Command(BaseCommand):
    help = "Seed initial catalog data"

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()

        # Categories
        electronics, _ = Category.objects.get_or_create(name="Electronics", parent=None, defaults={"created_by": user, "updated_by": user})
        apparel, _ = Category.objects.get_or_create(name="Apparel", parent=None, defaults={"created_by": user, "updated_by": user})
        Category.objects.get_or_create(name="Mobiles", parent=electronics, defaults={"created_by": user, "updated_by": user})
        Category.objects.get_or_create(name="Men", parent=apparel, defaults={"created_by": user, "updated_by": user})

        # Tax Rates
        for name, pct in [("GST 0%", Decimal("0")), ("GST 5%", Decimal("5")), ("GST 12%", Decimal("12")), ("GST 18%", Decimal("18"))]:
            TaxRate.objects.get_or_create(name=name, defaults={"percent": pct, "created_by": user, "updated_by": user})

        # UoMs
        pcs, _ = UoM.objects.get_or_create(code="PCS", defaults={"name": "Pieces", "ratio_to_base": Decimal("1.0"), "base": True, "created_by": user, "updated_by": user})
        UoM.objects.get_or_create(code="BOX", defaults={"name": "Box", "ratio_to_base": Decimal("10"), "base": False, "created_by": user, "updated_by": user})
        kg, _ = UoM.objects.get_or_create(code="KG", defaults={"name": "Kilogram", "ratio_to_base": Decimal("1.0"), "base": True, "created_by": user, "updated_by": user})
        UoM.objects.get_or_create(code="G", defaults={"name": "Gram", "ratio_to_base": Decimal("1000"), "base": False, "created_by": user, "updated_by": user})

        self.stdout.write(self.style.SUCCESS("Catalog seed complete."))
