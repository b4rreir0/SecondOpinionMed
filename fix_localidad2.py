#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from medicos.models import Localidad, ComiteMultidisciplinario
from cases.models import Case

# 1. Asignar el comite de pulmon a la localidad de pulmon (ID 2)
print("=== Asignando comite a localidad ===")
localidad_pulmon = Localidad.objects.get(id=2)
comite_pulmon = ComiteMultidisciplinario.objects.get(nombre__icontains='Pulmon')

print(f'Localidad: {localidad_pulmon.nombre}')
print(f'Comite: {comite_pulmon.nombre}')

localidad_pulmon.comite = comite_pulmon
localidad_pulmon.save()
print('Asignacion guardada')

# 2. Asignar el caso al primer medico del comite
print()
print("=== Actualizando caso ===")
caso = Case.objects.get(case_id='CASO-8EF5EC0AD025')
print(f'Caso: {caso.case_id}')
print(f'Doctor actual: {caso.doctor.email}')

# Obtener los medicos del comite de pulmon
medicos_pulmon = comite_pulmon.medicos_miembros.all()
print(f'Medicos del comite: {medicos_pulmon.count()}')
for m in medicos_pulmon:
    print(f'  - {m.nombres} {m.apellidos} ({m.usuario.email})')

# Asignar al primer medico del comite como responsable
if medicos_pulmon.exists():
    primer_medico = medicos_pulmon.first()
    caso.doctor = primer_medico.usuario
    caso.save()
    print(f'Caso asignado a: {primer_medico.usuario.email}')

print()
print("=== Verificacion final ===")
caso = Case.objects.get(case_id='CASO-8EF5EC0AD025')
print(f'Caso: {caso.case_id}')
print(f'Doctor asignado: {caso.doctor.email}')
print(f'Localidad: {caso.localidad.nombre}')
print(f'Comite de la localidad: {caso.localidad.comite.nombre}')
