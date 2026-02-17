#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from medicos.models import Localidad, ComiteMultidisciplinario

# Ver nombres exactos
print('=== Localidades (nombres exactos) ===')
for l in Localidad.objects.all():
    print(f'ID {l.id}: {repr(l.nombre)}')

print()
print('=== Comites (nombres exactos) ===')
for c in ComiteMultidisciplinario.objects.all():
    print(f'{repr(c.nombre)}')
