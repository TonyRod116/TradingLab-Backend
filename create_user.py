#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create test user
username = 'testuser'
email = 'test@example.com'
password = 'testpass123'

user, created = User.objects.get_or_create(
    username=username,
    defaults={'email': email}
)

user.set_password(password)
user.save()

if created:
    print(f"✅ User '{username}' created successfully!")
else:
    print(f"✅ User '{username}' updated successfully!")

print(f"Username: {username}")
print(f"Password: {password}")
print(f"Email: {email}")
