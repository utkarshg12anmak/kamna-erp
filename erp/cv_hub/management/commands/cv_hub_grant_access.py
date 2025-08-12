from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from django.db import transaction

class Command(BaseCommand):
    help = 'Grant CV Hub access to all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--group',
            type=str,
            default='CvHubAdmin',
            help='Group to assign to users (default: CvHubAdmin)',
            choices=['CvHubAdmin', 'CvHubViewer', 'Sales', 'Purchase']
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        group_name = options['group']
        dry_run = options['dry_run']
        
        self.stdout.write(f'Granting CV Hub access to all users...')
        self.stdout.write(f'Target group: {group_name}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            # Get the target group
            group = Group.objects.get(name=group_name)
            self.stdout.write(f'Found group: {group.name}')
            
            # Get all users
            users = User.objects.all()
            self.stdout.write(f'Found {users.count()} users')
            
            if users.count() == 0:
                self.stdout.write(self.style.WARNING('No users found in the system'))
                return
            
            # Show users that will be affected
            self.stdout.write('\nUsers to be granted access:')
            for user in users:
                status = "already has access" if group in user.groups.all() else "will get access"
                self.stdout.write(f'  - {user.username} ({user.get_full_name() or "No name"}) - {status}')
            
            if not dry_run:
                with transaction.atomic():
                    # Add all users to the group
                    users_added = 0
                    for user in users:
                        if group not in user.groups.all():
                            user.groups.add(group)
                            users_added += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully granted CV Hub access to {users_added} users '
                            f'(out of {users.count()} total users) via group "{group_name}"'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'DRY RUN: Would grant CV Hub access to users via group "{group_name}"'
                    )
                )
                
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Group "{group_name}" not found. Please run "python manage.py cv_hub_bootstrap_roles" first.'
                )
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error granting access: {str(e)}')
            )
            raise

        # Show permission summary
        self.stdout.write('\nCV Hub Permission Summary:')
        self.stdout.write('=========================')
        
        if not dry_run:
            for group_name in ['CvHubAdmin', 'CvHubViewer', 'Sales', 'Purchase']:
                try:
                    grp = Group.objects.get(name=group_name)
                    user_count = grp.user_set.count()
                    perm_count = grp.permissions.count()
                    self.stdout.write(f'{group_name}: {user_count} users, {perm_count} permissions')
                except Group.DoesNotExist:
                    self.stdout.write(f'{group_name}: Group not found')
        
        self.stdout.write('\nAccess granted! Users can now access CV Hub module.')
        self.stdout.write('URL: /app/cv_hub/')
