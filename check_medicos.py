#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from medicos.models import ComiteMultidisciplinario, Medico
from authentication.models import CustomUser

# Ver comités
print('=== Comités ===')
comites = ComiteMultidisciplinario.objects.all()
for c in comites:
    print(f'{c.nombre}:')
    for m in c.medicos_miembros.all():
        print(f'  - {m.nombres} {m.apellidos} ({m.usuario.email})')

# Ver médico de german
print()
print('=== Médico grm4nb4rreir0@gmail.com ===')
user = CustomUser.objects.filter(email='grm4nb4rreir0@gmail.com').first()
if user:
    if hasattr(user, 'medico'):
        medico = user.medico
        print(f'Medico ID: {medico.id}')
        print(f'Nombres: {medico.nombres} {medico.apellidos}')
        print(f'Comités: {list(c.nombre for c in medico.comites.all())}')
    else:
        print('No tiene Medico')

# Ver todos los médicos
print()
print('=== Todos los Médicos ===')
medicos = Medico.objects.all()
for m in medicos:
    print(f'{m.id}: {m.nombres} {m.apellidos} ({m.usuario.email}) - Comités: {list(c.nombre for c in m.comites.all())}')
