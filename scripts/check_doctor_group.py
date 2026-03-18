#!/usr/bin/env python
"""Script para consultar los médicos y sus grupos"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')

django.setup()

from medicos.models import MedicalGroup, DoctorGroupMembership, Medico
from authentication.models import CustomUser

print("="*60)
print("CONSULTA DE MÉDICOS Y GRUPOS")
print("="*60)

# Buscar el grupo de Tumores Toracicos
grupo_toracico = MedicalGroup.objects.filter(nombre__icontains='Toracico').first()
if grupo_toracico:
    print(f'\n--- GRUPO: {grupo_toracico.nombre} (ID: {grupo_toracico.id}) ---')
    
    # Ver memberships de este grupo
    memberships = DoctorGroupMembership.objects.filter(grupo=grupo_toracico, activo=True)
    print(f'Miembros activos en el grupo: {memberships.count()}')
    
    for m in memberships:
        print(f'\n  - Médico: {m.medico}')
        print(f'    Usuario: {m.medico.usuario}')
        print(f'    Activo: {m.activo}')
        print(f'    Asignación automática: {m.asignacion_auto}')
        if m.medico.usuario:
            print(f'    Email: {m.medico.usuario.email}')
else:
    print('\n** GRUPO NO ENCONTRADO **')

print('\n--- TODOS LOS GRUPOS Y SUS MIEMBROS ---')
for grupo in MedicalGroup.objects.all():
    print(f'\n{grupo.nombre} (ID: {grupo.id})')
    memberships = DoctorGroupMembership.objects.filter(grupo=grupo, activo=True)
    print(f'  Miembros activos: {memberships.count()}')
    for m in memberships:
        print(f'    - {m.medico.usuario.email if m.medico.usuario else "Sin usuario"}')
