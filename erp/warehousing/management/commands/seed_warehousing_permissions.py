from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from warehousing.models import Warehouse, Location, StockLedger, AdjustmentRequest


class Command(BaseCommand):
    help = "Create 'Warehousing' group and assign model permissions (view/add/change/delete) for warehousing models."

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name="Warehousing")
        models_full = [Warehouse, Location, AdjustmentRequest]
        models_view_only = [StockLedger]
        added = 0
        # Full CRUD where applicable
        for model in models_full:
            ct = ContentType.objects.get_for_model(model)
            for action in ["view", "add", "change", "delete"]:
                codename = f"{action}_{model._meta.model_name}"
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    group.permissions.add(perm)
                    added += 1
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Permission missing: {codename}"))
        # View only for ledger (ensure at least view permission exists)
        for model in models_view_only:
            ct = ContentType.objects.get_for_model(model)
            for action in ["view"]:
                codename = f"{action}_{model._meta.model_name}"
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    group.permissions.add(perm)
                    added += 1
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Permission missing: {codename}"))
        self.stdout.write(self.style.SUCCESS(f"Warehousing group ready. Permissions linked: {added}"))
