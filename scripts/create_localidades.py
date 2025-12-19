import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
import django
django.setup()

from medicos.models import Localidad

CANCER_TYPES = [
    'Cáncer de mama',
    'Cáncer de pulmón',
    'Cáncer de próstata',
    'Cáncer colorrectal',
    'Leucemia',
    'Linfoma',
    'Melanoma',
    'Cáncer de ovario',
    'Cáncer de páncreas',
    'Cáncer gástrico',
    'Cáncer de cabeza y cuello',
    'Cáncer de hígado'
]

created = 0
for name in CANCER_TYPES:
    obj, created_flag = Localidad.objects.get_or_create(nombre=name)
    if created_flag:
        created += 1
        print('Creada localidad:', name)
    else:
        print('Ya existe localidad:', name)

print(f'Total creadas: {created}')
