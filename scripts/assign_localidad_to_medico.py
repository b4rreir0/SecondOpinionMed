import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from medicos.models import Localidad, Medico

User = get_user_model()

EMAIL = 'grm4nb4rreir0@gmail.com'
LOCALIDAD_NAME = 'Cáncer de pulmón'

user = User.objects.filter(email__iexact=EMAIL).first()
if not user:
    print('No se encontró usuario con email', EMAIL)
    sys.exit(1)

medico = Medico.objects.filter(usuario=user).first()
if not medico:
    print('No se encontró perfil Medico para el usuario', EMAIL)
    sys.exit(1)

loc = Localidad.objects.filter(nombre__iexact=LOCALIDAD_NAME).first()
if not loc:
    print('No se encontró Localidad con nombre', LOCALIDAD_NAME)
    sys.exit(1)

loc.medico = medico
loc.save()
print(f'Localidad "{loc.nombre}" asignada al médico {medico.nombre_completo} ({EMAIL})')
