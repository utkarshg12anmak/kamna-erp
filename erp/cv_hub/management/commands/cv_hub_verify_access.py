from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User, Permission
from django.test import Client
from django.db import connection
from cv_hub.models import CvHubEntry
import json

class Command(BaseCommand):
    help = 'Verify CV Hub access and permissions for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed permission breakdown',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        
        self.stdout.write('🔐 CV Hub Access Verification')
        self.stdout.write('=' * 50)
        
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write('✅ Database connection: OK')
        except Exception as e:
            self.stdout.write(f'❌ Database connection: ERROR - {e}')
            return
        
        # Check CV Hub data
        try:
            entry_count = CvHubEntry.objects.count()
            self.stdout.write(f'✅ CV Hub entries: {entry_count} found')
        except Exception as e:
            self.stdout.write(f'❌ CV Hub data access: ERROR - {e}')
        
        # Check groups and permissions
        self.stdout.write('\n📋 Group Summary:')
        self.stdout.write('-' * 30)
        
        cv_hub_groups = ['CvHubAdmin', 'CvHubViewer', 'Sales', 'Purchase']
        
        for group_name in cv_hub_groups:
            try:
                group = Group.objects.get(name=group_name)
                user_count = group.user_set.count()
                perm_count = group.permissions.count()
                self.stdout.write(f'{group_name:12} | {user_count:2} users | {perm_count:2} permissions')
                
                if detailed:
                    users = list(group.user_set.values_list('username', flat=True))
                    if users:
                        self.stdout.write(f'             | Users: {", ".join(users)}')
                    
            except Group.DoesNotExist:
                self.stdout.write(f'{group_name:12} | NOT FOUND')
        
        # Check individual user access
        self.stdout.write('\n👥 User Access Test:')
        self.stdout.write('-' * 40)
        
        users = User.objects.all()
        if not users.exists():
            self.stdout.write('⚠️  No users found in system')
            return
        
        client = Client()
        
        for user in users:
            self.stdout.write(f'\nUser: {user.username} ({user.get_full_name() or "No name"})')
            
            # Check group memberships
            cv_groups = user.groups.filter(name__in=cv_hub_groups).values_list('name', flat=True)
            if cv_groups:
                self.stdout.write(f'  Groups: {", ".join(cv_groups)}')
            else:
                self.stdout.write('  Groups: None')
            
            # Test web access
            client.force_login(user)
            
            # Dashboard test
            try:
                response = client.get('/app/cv_hub/')
                status = '✅' if response.status_code == 200 else '❌'
                self.stdout.write(f'  Dashboard: {status} (HTTP {response.status_code})')
            except Exception as e:
                self.stdout.write(f'  Dashboard: ❌ Error - {str(e)[:50]}...')
            
            # Entries list test
            try:
                response = client.get('/app/cv_hub/entries/')
                status = '✅' if response.status_code == 200 else '❌'
                self.stdout.write(f'  Entries:   {status} (HTTP {response.status_code})')
            except Exception as e:
                self.stdout.write(f'  Entries:   ❌ Error - {str(e)[:50]}...')
            
            # API test
            try:
                response = client.get('/api/cv_hub/entries/')
                if response.status_code == 200:
                    data = response.json()
                    count = data.get('count', len(data.get('results', [])))
                    self.stdout.write(f'  API:       ✅ (HTTP {response.status_code}) - {count} entries')
                else:
                    self.stdout.write(f'  API:       ❌ (HTTP {response.status_code})')
            except Exception as e:
                self.stdout.write(f'  API:       ❌ Error - {str(e)[:50]}...')
        
        # Overall summary
        self.stdout.write('\n📊 Summary:')
        self.stdout.write('-' * 20)
        
        total_users = users.count()
        users_with_access = User.objects.filter(
            groups__name__in=cv_hub_groups
        ).distinct().count()
        
        self.stdout.write(f'Total users:           {total_users}')
        self.stdout.write(f'Users with CV Hub:     {users_with_access}')
        self.stdout.write(f'Coverage:              {(users_with_access/total_users*100):.1f}%')
        
        # Recommendations
        if users_with_access < total_users:
            missing_users = User.objects.exclude(
                groups__name__in=cv_hub_groups
            ).values_list('username', flat=True)
            self.stdout.write(f'\n⚠️  Users without access: {", ".join(missing_users)}')
            self.stdout.write('💡 Run: python manage.py cv_hub_grant_access --group CvHubAdmin')
        else:
            self.stdout.write('\n✅ All users have CV Hub access!')
        
        self.stdout.write('\n🏢 CV Hub Module: READY')
        self.stdout.write('   Dashboard: /app/cv_hub/')
        self.stdout.write('   Entries:   /app/cv_hub/entries/')
        self.stdout.write('   API:       /api/cv_hub/entries/')
