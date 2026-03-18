#!/usr/bin/env python
"""Script para verificar y corregir la asignación al coordinador"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')

django.setup()

from cases.models import Case
from medicos.models import MedicalGroup, DoctorGroupMembership

print("="*60)
print("VERIFICACIÓN DEL COORDINADOR DEL GRUPO")
print("="*60)

# Buscar el grupo de Tumores Toracicos
grupo = MedicalGroup.objects.filter(nombre__icontains='Toracico').first()
if grupo:
    print(f'\n--- GRUPO: {grupo.nombre} (ID: {grupo.id}) ---')
    
    # Ver el coordinador del grupo
    print(f'Coordinador del grupo: {grupo.coordinador}')
    
    # Ver las membresías con rol de coordinador
    membresias_coordinador = DoctorGroupMembership.objects.filter(
        grupo=grupo, 
        rol='coordinador',
        activo=True
    )
    print(f'Membresías con rol coordinador: {membershipes_coordinador.count()}')
    for m in membresias_coordinador:
        print(f'  - {m.medico.nombre_completo} ({m.medico.usuario.email if m.medico.usuario else "Sin email"})')
else:
    print('\n** GRUPO NO ENCONTRADO **')
