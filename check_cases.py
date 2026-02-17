#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from cases.models import Case
from authentication.models import CustomUser

# Ver casos recientes
print('=== Casos recientes ===')
casos = Case.objects.all().order_by('-created_at')[:10]
for c in casos:
    print(f'ID: {c.case_id}')
    print(f'  Paciente: {c.patient.email}')
    print(f'  Estado: {c.status}')
    print(f'  Localidad: {c.localidad.nombre if c.localidad else "Sin localidad"}')
    print(f'  Doctor: {c.doctor.email if c.doctor else "Sin asignar"}')
    print(f'  Creado: {c.created_at}')
    print()

# Ver usuario german
print('=== Usuario germanbarreiro2121@gmail.com ===')
user = CustomUser.objects.filter(email='germanbarreiro2121@gmail.com').first()
if user:
    print(f'Email: {user.email}')
    print(f'Rol: {user.role}')
else:
    print('Usuario no encontrado')

# Ver casos del usuario german
print()
print('=== Casos del usuario germanbarreiro2121@gmail.com ===')
user = CustomUser.objects.filter(email='germanbarreiro2121@gmail.com').first()
if user:
    casos_german = Case.objects.filter(patient=user)
    print(f'Total: {casos_german.count()}')
    for c in casos_german:
        print(f'  - {c.case_id}: {c.status} - Localidad: {c.localidad.nombre if c.localidad else "Sin"}')
