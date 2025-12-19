import os, sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

EMAIL = 'germanbarreiro2121@gmail.com'
user = User.objects.filter(email__iexact=EMAIL).first()
if not user:
    print('No user found for', EMAIL)
    sys.exit(0)

try:
    from cases.models import Case
except Exception:
    Case = None

if Case:
    qs = Case.objects.filter(patient=user)
    print('Found', qs.count(), 'cases for', EMAIL)
    for c in qs:
        loc = getattr(c.localidad, 'nombre', None)
        doc_email = getattr(getattr(c.doctor, 'email', None), 'lower', lambda: c.doctor)()
        print(f'{c.case_id} | status={c.status} | localidad={loc} | doctor={getattr(c.doctor, "email", None)}')
else:
    print('Case model not available')
