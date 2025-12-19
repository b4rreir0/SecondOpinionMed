import os,sys
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','oncosegunda.settings')
import django
django.setup()
from cases.models import Case

count=0
for c in Case.objects.filter(doctor__isnull=True).exclude(localidad__isnull=True):
    loc = c.localidad
    medico = getattr(loc, 'medico', None)
    user = getattr(medico, 'usuario', None)
    if user:
        from cases.services import CaseService
        try:
            CaseService.assign_case_to_doctor(c, user)
            print(f'Assigned case {c.case_id} to {user.email}')
            count += 1
        except Exception as e:
            print('Error assigning', c.case_id, e)
    else:
        print(f'Localidad {loc.nombre} has no medico usuario')

print('Total assigned:', count)
