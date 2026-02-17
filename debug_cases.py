#!/usr/bin/env python
"""
Script para depurar los casos y verificar la asignación
"""
import os
import sys
import django

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')

# Inicializar Django
django.setup()

from django.contrib.auth import get_user_model
from cases.models import Case
from medicos.models import Medico, Localidad, ComiteMultidisciplinario

User = get_user_model()

print("=" * 60)
print("DEBUG: Verificando casos y médicos")
print("=" * 60)

# Ver todos los casos
print("\n--- TODOS LOS CASOS ---")
todos_casos = Case.objects.all()
print(f"Total: {todos_casos.count()}")
for c in todos_casos:
    print(f"  - {c.case_id}")
    print(f"    Status: {c.status}")
    print(f"    Doctor: {c.doctor}")
    print(f"    Localidad: {c.localidad}")
    if c.localidad:
        print(f"    Localidad.nombre: {c.localidad.nombre}")
        if c.localidad.comite:
            print(f"    Localidad.comite: {c.localidad.comite.nombre}")
    print()

# Ver todos los médicos con sus usuarios
print("\n--- MÉDICOS CON USUARIOS ---")
medicos = Medico.objects.all()
print(f"Total: {medicos.count()}")
for m in medicos:
    print(f"  - {m.usuario.email}")
    print(f"    Nombre: {m.nombres} {m.apellidos}")
    print(f"    Estado: {m.estado}")
    comites = m.comites.all()
    print(f"    Comités: {comites.count()}")
    for c in comites:
        print(f"      - {c.nombre}")
    print()

# Ver todas las localidades
print("\n--- LOCALIDADES ---")
localidades = Localidad.objects.all()
print(f"Total: {localidades.count()}")
for l in localidades:
    print(f"  - {l.nombre}")
    if l.comite:
        print(f"    Comité: {l.comite.nombre}")
    print()

# Ver el usuario específico del doctor
print("\n--- USUARIO DEL DOCTOR (dr.garcia@oncosegunda.com) ---")
try:
    doctor_user = User.objects.get(email='dr.garcia@oncosegunda.com')
    print(f"Usuario: {doctor_user.email}")
    print(f"Role: {doctor_user.role}")
    print(f"is_active: {doctor_user.is_active}")
    
    # Verificar si tiene objeto Medico
    if hasattr(doctor_user, 'medico'):
        medico = doctor_user.medico
        print(f"Medico: {medico.nombres} {medico.apellidos}")
        print(f"Estado medico: {medico.estado}")
        comites = medico.comites.all()
        print(f"Comités: {comites.count()}")
        for c in comites:
            print(f"  - {c.nombre}")
            # Ver localidades de este comité
            locs = Localidad.objects.filter(comite=c)
            print(f"    Localidades: {locs.count()}")
            for loc in locs:
                print(f"      - {loc.nombre}")
    else:
        print("NO tiene objeto Medico!")
except User.DoesNotExist:
    print("Usuario no encontrado!")

# Verificar casos asignados al doctor
print("\n--- CASOS ASIGNADOS AL DOCTOR ---")
try:
    doctor_user = User.objects.get(email='dr.garcia@oncosegunda.com')
    casos_doctor = Case.objects.filter(doctor=doctor_user)
    print(f"Casos donde es doctor asignado: {casos_doctor.count()}")
    for c in casos_doctor:
        print(f"  - {c.case_id}: status={c.status}")
    
    # Ahora probar la función del servicio
    print("\n--- PROBANDO CaseService.get_doctor_assigned_cases ---")
    from cases.services import CaseService
    casos_asignados = CaseService.get_doctor_assigned_cases(doctor_user)
    print(f"Casos asignados (total): {casos_asignados.count()}")
    for c in casos_asignados:
        print(f"  - {c.case_id}: status={c.status}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("FIN DEL DEBUG")
print("=" * 60)
