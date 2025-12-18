import os
import django
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')

# Ensure project root is on sys.path so Django can import the settings package
import sys
sys.path.insert(0, str(BASE_DIR))

django.setup()

from authentication.models import CustomUser

EMAIL = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', None)
if not PASSWORD:
    # generate a secure random password
    PASSWORD = secrets.token_urlsafe(12)

username = EMAIL

if CustomUser.objects.filter(email=EMAIL).exists():
    print(f"Admin user with email {EMAIL} already exists.")
else:
    user = CustomUser.objects.create_superuser(username=username, email=EMAIL, password=PASSWORD)
    user.is_active = True
    user.save()
    creds_file = BASE_DIR / 'ADMIN_CREDENTIALS.txt'
    with open(creds_file, 'w') as f:
        f.write(f"ADMIN_EMAIL={EMAIL}\n")
        f.write(f"ADMIN_PASSWORD={PASSWORD}\n")
    print(f"Created admin user {EMAIL}. Credentials saved to {creds_file}")

print('Done')
