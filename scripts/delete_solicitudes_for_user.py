import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from pacientes.models import Paciente, CasoClinico, SolicitudSegundaOpinion

User = get_user_model()

EMAIL = 'germanbarreiro2121@gmail.com'

user = User.objects.filter(email__iexact=EMAIL).first()
if not user:
    print('No se encontró usuario con email', EMAIL)
    sys.exit(1)

paciente = Paciente.objects.filter(usuario=user).first()
if not paciente:
    print('El usuario no tiene perfil Paciente asociado:', EMAIL)
    sys.exit(1)

casos = CasoClinico.objects.filter(paciente=paciente)
count = 0
for caso in casos:
    try:
        solicitud = caso.solicitud
    except SolicitudSegundaOpinion.DoesNotExist:
        solicitud = None
    if solicitud:
        solicitud.delete()
        count += 1
        print(f'Solicitud eliminada para caso {caso.uuid}')

print(f'Total solicitudes eliminadas: {count}')
