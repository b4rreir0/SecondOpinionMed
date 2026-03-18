#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
django.setup()

from apps.cases.models import Case
from apps.medicos.models import TipoCancer, MedicalGroup

# Ver el caso específico
print("="*60)
print("CONSULTA DE DATOS DEL CASO CASO-3DA8DACF2263")
print("="*60)

caso = Case.objects.filter(case_id='CASO-3DA8DACF2263').first()
if caso:
    print('\n=== DATOS DEL CASO ===')
    print(f'Case ID: {caso.case_id}')
    print(f'Status: {caso.status}')
    print(f'Primary Diagnosis: {caso.primary_diagnosis}')
    print(f'Doctor: {caso.doctor}')
    print(f'Medical Group: {caso.medical_group}')
    print(f'Tipo Cancer: {caso.tipo_cancer}')
    if caso.tipo_cancer:
        print(f'  - Tipo Cancer Codigo: {caso.tipo_cancer.codigo}')
        print(f'  - Tipo Cancer Grupo Medico: {caso.tipo_cancer.grupo_medico}')
    print(f'Localidad: {caso.localidad}')
else:
    print('Caso no encontrado')

print('\n=== TODOS LOS CASOS ===')
for c in Case.objects.all():
    print(f'{c.case_id}: status={c.status}, tipo_cancer={c.tipo_cancer}, medical_group={c.medical_group}')

print('\n=== TIPOS DE CANCER ===')
for tc in TipoCancer.objects.all():
    print(f'{tc.codigo}: {tc.nombre} -> Grupo: {tc.grupo_medico}')

print('\n=== GRUPOS MEDICOS ===')
for mg in MedicalGroup.objects.all():
    print(f'{mg.nombre}: {mg.tipos_cancer.count()} tipos de cancer')
