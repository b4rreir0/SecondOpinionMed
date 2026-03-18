#!/usr/bin/env python
"""Script para reasignar el caso al coordinador"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')

django.setup()

from cases.models import Case
from cases.services import asignar_caso_automatico

print("="*60)
print("REASIGNACIÓN DEL CASO AL COORDINADOR")
print("="*60)

# Buscar el caso
caso = Case.objects.filter(case_id='CASO-3DA8DACF2263').first()
if caso:
    print(f'\n--- CASO ACTUALMENTE ---')
    print(f'Case ID: {caso.case_id}')
    print(f'Status: {caso.status}')
    print(f'Medical Group: {caso.medical_group}')
    print(f'Responsable (antes): {caso.responsable}')
    print(f'Doctor (antes): {caso.doctor}')
    
    # Reasignar el caso
    print('\n--- EJECUTANDO REASIGNACIÓN ---')
    resultado = asignar_caso_automatico(caso)
    print(f'Resultado: {resultado}')
    
    # Verificar el caso después
    caso.refresh_from_db()
    print(f'\n--- CASO DESPUÉS ---')
    print(f'Medical Group: {caso.medical_group}')
    print(f'Responsable (después): {caso.responsable}')
    print(f'Doctor (después): {caso.doctor}')
else:
    print('\n** CASO NO ENCONTRADO **')
