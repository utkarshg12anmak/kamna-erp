#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from django.contrib.auth.models import Group, User

# Create group with exact module name
group, created = Group.objects.get_or_create(name='Customer & Vendor Hub')
if created:
    print('Created group: Customer & Vendor Hub')
else:
    print('Group already exists: Customer & Vendor Hub')

# Get the CvHubAdmin group permissions and copy them
cv_hub_admin = Group.objects.get(name='CvHubAdmin')
permissions = cv_hub_admin.permissions.all()
group.permissions.set(permissions)
print(f'Copied {permissions.count()} permissions to Customer & Vendor Hub group')

# Add all users to this group
users = User.objects.all()
for user in users:
    group.user_set.add(user)
    print(f'Added {user.username} to Customer & Vendor Hub group')

print('CV Hub access setup completed!')

# Verify the setup
print('\nVerification:')
for user in User.objects.all():
    cv_groups = user.groups.filter(name__contains='Hub').values_list('name', flat=True)
    print(f'{user.username}: {list(cv_groups)}')
