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
from django.utils import timezone

User = get_user_model()

EMAIL = 'grm4nb4rreir0@gmail.com'
LOCALIDAD_NAME = 'Cáncer de pulmón'

user = User.objects.filter(email__iexact=EMAIL).first()
if not user:
    print('No se encontró usuario con email', EMAIL)
    sys.exit(1)

medico = Medico.objects.filter(usuario=user).first()
loc = Localidad.objects.filter(nombre__iexact=LOCALIDAD_NAME).first()
if not loc:
    print('No se encontró Localidad con nombre', LOCALIDAD_NAME)
    sys.exit(1)

if medico:
    loc.medico = medico
    loc.save()
    print(f'Localidad "{loc.nombre}" asignada al médico existente {medico.nombre_completo} ({EMAIL})')
    sys.exit(0)

# Crear perfil Medico mínimo
numero_documento = f"doc{user.pk}{int(timezone.now().timestamp())%100000}"
registro_medico = f"REG{user.pk}{int(timezone.now().timestamp())%100000}"

nombres = user.first_name or (user.get_full_name().split(' ')[0] if user.get_full_name() else 'Nombre')
apellidos = user.last_name or (user.get_full_name().split(' ')[1] if len(user.get_full_name().split(' '))>1 else 'Apellido')

medico = Medico.objects.create(
    usuario=user,
    tipo_documento='cc',
    numero_documento=numero_documento,
    nombres=nombres,
    apellidos=apellidos,
    fecha_nacimiento='1980-01-01',
    genero='otro',
    registro_medico=registro_medico,
    institucion_actual='No definida',
    telefono='+000000000',
)

loc.medico = medico
loc.save()
print(f'Perfil Medico creado y localidad "{loc.nombre}" asignada a {medico.nombre_completo} ({EMAIL})')
