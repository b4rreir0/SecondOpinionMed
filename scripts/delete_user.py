# Script to delete a user by email and related DB rows/files
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'

# Load .env (simple parser)
if ENV_PATH.exists():
    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        for raw in f.readlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings'))

import django
import sys
# Ensure project BASE_DIR and apps/ are on sys.path so Django can import apps
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
APPS_DIR = BASE_DIR / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

django.setup()

from django.conf import settings
# Import using the app package name (apps/ is on sys.path so package is 'authentication')
from authentication.models import CustomUser

EMAIL = 'grm4nb4rreir0@gmail.com'

user_qs = CustomUser.objects.filter(email=EMAIL)
if not user_qs.exists():
    print(f"No user found with email {EMAIL}")
    sys.exit(0)

user = user_qs.first()
print(f"Found user id={user.id} email={user.email} username={user.username}")

# Collect files to delete (CaseDocument.file and user-related filefields)
files_to_delete = []

# Case documents
try:
    from apps.cases.models import CaseDocument
    docs = CaseDocument.objects.filter(case__patient=user)
    for d in docs:
        if d.file:
            path = d.file.path if hasattr(d.file, 'path') else None
            if path:
                files_to_delete.append(path)
except Exception:
    pass

# Uploaded documents by user
try:
    docs2 = CaseDocument.objects.filter(uploaded_by=user)
    for d in docs2:
        if d.file:
            path = d.file.path if hasattr(d.file, 'path') else None
            if path:
                files_to_delete.append(path)
except Exception:
    pass

# Patient profile may not have files, but check common fields named 'profile_image' etc.
try:
    profile = getattr(user, 'patient_profile', None) or getattr(user, 'doctor_profile', None)
    if profile:
        for field in getattr(profile, '_meta').get_fields():
            if getattr(field, 'get_internal_type', lambda: '')() == 'FileField':
                val = getattr(profile, field.name)
                if val and hasattr(val, 'path'):
                    files_to_delete.append(val.path)
except Exception:
    pass

# Remove DB entries by deleting the user (cascades)
user_id = user.id
user.delete()
print(f"Deleted user and cascaded related DB rows for user id {user_id}")

# Delete files from disk
MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', str(BASE_DIR / 'media'))
removed = 0
for p in set(files_to_delete):
    try:
        p = os.path.abspath(p)
        if os.path.commonpath([p, os.path.abspath(MEDIA_ROOT)]) != os.path.abspath(MEDIA_ROOT):
            print(f"Skipping file outside MEDIA_ROOT: {p}")
            continue
        if os.path.exists(p):
            os.remove(p)
            removed += 1
            print(f"Removed file: {p}")
    except Exception as e:
        print(f"Error removing file {p}: {e}")

print(f"Finished. Files removed: {removed}")
