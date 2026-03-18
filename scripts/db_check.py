#!/usr/bin/env python
"""Script para consultar los datos del caso"""
import os
import sys
import django

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')

# Setup Django
django.setup()

from cases.models import Case
from medicos.models import TipoCancer, MedicalGroup, DoctorGroupMembership, Medico

print("="*60)
print("CONSULTA DE DATOS - CASO CASO-3DA8DACF2263")
print("="*60)

# Ver el caso específico
caso = Case.objects.filter(case_id='CASO-3DA8DACF2263').first()
if caso:
    print('\n--- DATOS DEL CASO ---')
    print(f'Case ID: {caso.case_id}')
    print(f'Status: {caso.status}')
    print(f'Primary Diagnosis: {caso.primary_diagnosis}')
    print(f'Doctor (usuario): {caso.doctor}')
    print(f'Medical Group: {caso.medical_group}')
    print(f'Tipo Cancer: {caso.tipo_cancer}')
    if caso.tipo_cancer:
        print(f'  -> Tipo Cancer Codigo: {caso.tipo_cancer.codigo}')
        print(f'  -> Tipo Cancer Grupo Medico (TipoCancer.grupo_medico): {caso.tipo_cancer.grupo_medico}')
    print(f'Localidad: {caso.localidad}')
else:
    print('\n** CASO NO ENCONTRADO **')

print('\n--- TODOS LOS CASOS EN LA BASE DE DATOS ---')
for c in Case.objects.all().order_by('-created_at'):
    print(f'{c.case_id}: status={c.status}, tipo_cancer={c.tipo_cancer}, medical_group={c.medical_group}')

print('\n--- TIPOS DE CANCER ---')
for tc in TipoCancer.objects.all():
    print(f'{tc.codigo}: {tc.nombre} -> grupo_medico={tc.grupo_medico}')

print('\n--- GRUPOS MEDICOS ---')
for mg in MedicalGroup.objects.all():
    print(f'{mg.nombre} ({mg.id}): tiene {mg.tipos_cancer.count()} tipos de cancer')
    for tc in mg.tipos_cancer.all():
        print(f'   - {tc.codigo}: {tc.nombre}')
