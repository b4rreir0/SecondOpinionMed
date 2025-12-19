import os,sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','oncosegunda.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from cases.services import CaseService
User = get_user_model()
EMAIL='grm4nb4rreir0@gmail.com'
user = User.objects.filter(email__iexact=EMAIL).first()
if not user:
    print('No such user',EMAIL); sys.exit(1)
qs = CaseService.get_doctor_assigned_cases(user)
print('Assigned cases count for',EMAIL,':',qs.count())
for c in qs:
    print('-',c.case_id,c.status)
