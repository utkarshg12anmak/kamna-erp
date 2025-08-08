from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from catalog.models import Brand, Category, TaxRate, UoM, Item

class Command(BaseCommand):
    help = "Create 'Catalog' group and assign model permissions (view/add/change/delete) for catalog models."

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name='Catalog')
        models = [Brand, Category, TaxRate, UoM, Item]
        added = 0
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            for action in ['view', 'add', 'change', 'delete']:
                codename = f"{action}_{model._meta.model_name}"
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    group.permissions.add(perm)
                    added += 1
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Permission missing: {codename}"))
        self.stdout.write(self.style.SUCCESS(f"Catalog group ready. Permissions linked: {added}"))
