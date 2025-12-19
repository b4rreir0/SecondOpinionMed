import os,sys
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','oncosegunda.settings')
import django
django.setup()
from cases.models import Case
from django.contrib.auth import get_user_model
User=get_user_model()

def assign(case_id, doctor_email):
    case = Case.objects.filter(case_id=case_id).first()
    doctor = User.objects.filter(email__iexact=doctor_email).first()
    print('Before:', case.case_id, 'doctor=', getattr(case.doctor,'email',None), 'status=', case.status)
    from cases.services import CaseService
    try:
        CaseService.assign_case_to_doctor(case, doctor)
        print('Assigned')
    except Exception as e:
        print('Error assigning:', e)
    case.refresh_from_db()
    print('After:', case.case_id, 'doctor=', getattr(case.doctor,'email',None), 'status=', case.status, 'assigned_at=', case.assigned_at)

if __name__ == '__main__':
    assign('CASO-426BD8F971DE', 'grm4nb4rreir0@gmail.com')
