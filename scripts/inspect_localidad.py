import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
import django
django.setup()

from medicos.models import Localidad

for loc in Localidad.objects.all():
    medico = getattr(loc, 'medico', None)
    email = getattr(getattr(medico, 'usuario', None), 'email', None)
    print(f'Localidad: {loc.nombre} | Medico: {getattr(medico, "nombre_completo", None)} | UsuarioEmail: {email}')
