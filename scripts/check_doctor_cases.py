#!/usr/bin/env python
"""Script para verificar si el doctor puede ver el caso"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')

django.setup()

from cases.models import Case
from cases.services import CaseService
from authentication.models import CustomUser

print("="*60)
print("VERIFICACIÓN DE CASOS PARA EL DOCTOR")
print("="*60)

# Buscar el caso
caso = Case.objects.filter(case_id='CASO-3DA8DACF2263').first()
if caso:
    print(f'\n--- CASO {caso.case_id} ---')
    print(f'Status: {caso.status}')
    print(f'Medical Group: {caso.medical_group}')
    print(f'Responsable: {caso.responsable}')
    print(f'Doctor: {caso.doctor}')
else:
    print('\n** CASO NO ENCONTRADO **')
    sys.exit(1)

# Buscar al doctor Jose Antonio Rodriguez Perez
doctor_user = CustomUser.objects.filter(email='dr.rodriguez@oncosegunda.com').first()
if doctor_user:
    print(f'\n--- CASOS VISIBLES PARA {doctor_user.email} ---')
    casos_asignados = CaseService.get_doctor_assigned_cases(doctor_user)
    print(f'Total de casos asignados: {casos_asignados.count()}')
    
    # Verificar si el caso específico está en la lista
    caso_en_lista = casos_asignados.filter(case_id='CASO-3DA8DACF2263').exists()
    print(f'CASO-3DA8DACF2263 visible: {caso_en_lista}')
    
    # Mostrar todos los casos visibles
    print('\nCasos visibles:')
    for c in casos_asignados:
        print(f'  - {c.case_id}: {c.status}, grupo={c.medical_group}')
else:
    print('\n** DOCTOR NO ENCONTRADO **')
