from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from customer_vendor_hub.models import Partner


class Command(BaseCommand):
    help = "Create groups and permissions for Customer & Vendor Hub"

    def handle(self, *args, **options):
        # Create a basic group with model perms
        group, _ = Group.objects.get_or_create(name="Partners")
        ct = ContentType.objects.get_for_model(Partner)
        perms = Permission.objects.filter(content_type=ct)
        group.permissions.add(*perms)
        self.stdout.write(self.style.SUCCESS("Bootstrapped Partners group and permissions."))
