#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from medicos.models import Localidad, ComiteMultidisciplinario, Medico
from cases.models import Case

# 1. Asignar el comité de pulmóm a la localidad de pulmóm
print("=== Asignando comite a localidad ===")
localidad_pulmon = Localidad.objects.filter(nombre__icontains='pulmon').first()
comite_pulmon = ComiteMultidisciplinario.objects.filter(nombre__icontains='Pulmon').first()

if localidad_pulmon and comite_pulmon:
    localidad_pulmon.comite = comite_pulmon
    localidad_pulmon.save()
    print(f'Localidad "{localidad_pulmon.nombre}" ahora tiene comite: {comite_pulmon.nombre}')
else:
    print(f'Localidad: {localidad_pulmon}, Comite: {comite_pulmon}')

# 2. Ver el caso y cambiar el doctor asignado
print()
print("=== Actualizando caso ===")
caso = Case.objects.filter(case_id='CASO-8EF5EC0AD025').first()
if caso:
    doctor_email = caso.doctor.email if caso.doctor else "Sin asignar"
    print(f'Caso: {caso.case_id}')
    print(f'Estado actual: {caso.status}')
    print(f'Doctor actual: {doctor_email}')
    
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
else:
    print('Caso no encontrado')

print()
print("=== Verificando asignacion ===")
caso = Case.objects.filter(case_id='CASO-8EF5EC0AD025').first()
if caso:
    doctor_email = caso.doctor.email if caso.doctor else "Sin asignar"
    localidad_nombre = caso.localidad.nombre if caso.localidad else "Sin localidad"
    comite_nombre = caso.localidad.comite.nombre if caso.localidad and caso.localidad.comite else "Sin comite"
    print(f'Caso: {caso.case_id}')
    print(f'Doctor asignado: {doctor_email}')
    print(f'Localidad: {localidad_nombre}')
    print(f'Comite de la localidad: {comite_nombre}')
