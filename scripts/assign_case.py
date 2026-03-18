#!/usr/bin/env python
"""Script para asignar el caso automáticamente"""
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
print("ASIGNACIÓN AUTOMÁTICA DEL CASO")
print("="*60)

# Buscar el caso
caso = Case.objects.filter(case_id='CASO-3DA8DACF2263').first()
if caso:
    print(f'\n--- CASO ACTUALMENTE ---')
    print(f'Case ID: {caso.case_id}')
    print(f'Status: {caso.status}')
    print(f'Tipo Cancer: {caso.tipo_cancer}')
    print(f'Medical Group (antes): {caso.medical_group}')
    
    if caso.tipo_cancer:
        print(f'Tipo Cancer Grupo Medico: {caso.tipo_cancer.grupo_medico}')
    
    # Verificar si necesita asignación
    if caso.status == 'SUBMITTED' and not caso.medical_group:
        print('\n--- EJECUTANDO ASIGNACIÓN AUTOMÁTICA ---')
        resultado = asignar_caso_automatico(caso)
        print(f'Resultado: {resultado}')
        
        # Verificar el caso después
        caso.refresh_from_db()
        print(f'\n--- CASO DESPUÉS ---')
        print(f'Medical Group (después): {caso.medical_group}')
        print(f'Responsable: {caso.responsable}')
        print(f'Doctor: {caso.doctor}')
    else:
        print('\n** NO SE CUMPLE LA CONDICIÓN PARA ASIGNAR **')
        print(f'Status es SUBMITTED: {caso.status == "SUBMITTED"}')
        print(f'Medical Group es None: {caso.medical_group is None}')
else:
    print('\n** CASO NO ENCONTRADO **')
