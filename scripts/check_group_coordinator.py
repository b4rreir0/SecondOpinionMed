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
    
    # Ver el responsable por defecto del grupo
    print(f'Responsable por defecto del grupo: {grupo.responsable_por_defecto}')
    
    # Ver las membresías con rol de coordinador
    membresias = DoctorGroupMembership.objects.filter(
        grupo=grupo, 
        rol='coordinador',
        activo=True
    )
    print(f'\nMembresías con rol coordinador: {membresias.count()}')
    for m in membresias:
        print(f'  - {m.medico.nombre_completo} ({m.medico.usuario.email if m.medico.usuario else "Sin email"})')
        
    # Si no hay responsable por defecto, asignar al coordinador
    if not grupo.responsable_por_defecto and membresias.exists():
        primer_coordinador = membresias.first().medico
        print(f'\n--- ASIGNANDO COORDINADOR COMO RESPONSABLE POR DEFECTO ---')
        grupo.responsable_por_defecto = primer_coordinador
        grupo.save()
        print(f'Ahora el responsable por defecto es: {grupo.responsable_por_defecto}')
else:
    print('\n** GRUPO NO ENCONTRADO **')
