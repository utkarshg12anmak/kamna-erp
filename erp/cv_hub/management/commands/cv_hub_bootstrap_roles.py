from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from cv_hub.models import CvHubEntry, CvHubGSTRegistration, CvHubAddress, CvHubContact

class Command(BaseCommand):
    help = 'Bootstrap CV Hub user groups and permissions'

    def handle(self, *args, **options):
        self.stdout.write('Creating CV Hub user groups and permissions...')
        
        # Get content types for CV Hub models
        entry_ct = ContentType.objects.get_for_model(CvHubEntry)
        gst_ct = ContentType.objects.get_for_model(CvHubGSTRegistration)
        address_ct = ContentType.objects.get_for_model(CvHubAddress)
        contact_ct = ContentType.objects.get_for_model(CvHubContact)
        
        # Define permissions for each model
        all_models_perms = [
            (entry_ct, ['add', 'change', 'delete', 'view']),
            (gst_ct, ['add', 'change', 'delete', 'view']),
            (address_ct, ['add', 'change', 'delete', 'view']),
            (contact_ct, ['add', 'change', 'delete', 'view']),
        ]
        
        # CV Hub Admin - Full access
        admin_group, created = Group.objects.get_or_create(name='CvHubAdmin')
        if created:
            self.stdout.write('Created group: CvHubAdmin')
        
        admin_perms = []
        for ct, perm_types in all_models_perms:
            for perm_type in perm_types:
                perm_codename = f'{perm_type}_{ct.model}'
                try:
                    perm = Permission.objects.get(
                        content_type=ct,
                        codename=perm_codename
                    )
                    admin_perms.append(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(f'Warning: Permission {perm_codename} not found')
        
        admin_group.permissions.set(admin_perms)
        self.stdout.write(f'Assigned {len(admin_perms)} permissions to CvHubAdmin')
        
        # Sales Group - Entries, addresses, contacts (for customer management)
        sales_group, created = Group.objects.get_or_create(name='Sales')
        if created:
            self.stdout.write('Created group: Sales')
        
        sales_perms = []
        sales_models = [(entry_ct, ['add', 'change', 'view']), 
                       (address_ct, ['add', 'change', 'view']), 
                       (contact_ct, ['add', 'change', 'view'])]
        
        for ct, perm_types in sales_models:
            for perm_type in perm_types:
                perm_codename = f'{perm_type}_{ct.model}'
                try:
                    perm = Permission.objects.get(
                        content_type=ct,
                        codename=perm_codename
                    )
                    sales_perms.append(perm)
                except Permission.DoesNotExist:
                    pass
        
        sales_group.permissions.set(sales_perms)
        self.stdout.write(f'Assigned {len(sales_perms)} permissions to Sales')
        
        # Purchase Group - All models (for supplier/vendor management)
        purchase_group, created = Group.objects.get_or_create(name='Purchase')
        if created:
            self.stdout.write('Created group: Purchase')
        
        purchase_perms = []
        purchase_models = [(entry_ct, ['add', 'change', 'view']), 
                          (gst_ct, ['add', 'change', 'view']),
                          (address_ct, ['add', 'change', 'view']), 
                          (contact_ct, ['add', 'change', 'view'])]
        
        for ct, perm_types in purchase_models:
            for perm_type in perm_types:
                perm_codename = f'{perm_type}_{ct.model}'
                try:
                    perm = Permission.objects.get(
                        content_type=ct,
                        codename=perm_codename
                    )
                    purchase_perms.append(perm)
                except Permission.DoesNotExist:
                    pass
        
        purchase_group.permissions.set(purchase_perms)
        self.stdout.write(f'Assigned {len(purchase_perms)} permissions to Purchase')
        
        # CV Hub Viewer - View only access
        viewer_group, created = Group.objects.get_or_create(name='CvHubViewer')
        if created:
            self.stdout.write('Created group: CvHubViewer')
        
        viewer_perms = []
        for ct, _ in all_models_perms:
            perm_codename = f'view_{ct.model}'
            try:
                perm = Permission.objects.get(
                    content_type=ct,
                    codename=perm_codename
                )
                viewer_perms.append(perm)
            except Permission.DoesNotExist:
                pass
        
        viewer_group.permissions.set(viewer_perms)
        self.stdout.write(f'Assigned {len(viewer_perms)} permissions to CvHubViewer')
        
        self.stdout.write(self.style.SUCCESS('CV Hub groups and permissions setup completed!'))
