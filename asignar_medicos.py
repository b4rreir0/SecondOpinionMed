#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
sys.path.insert(0, '.')

django.setup()

from medicos.models import Medico, MedicalGroup, DoctorGroupMembership

# Buscar grupo
g = MedicalGroup.objects.filter(nombre__icontains='Toracico').first()
print('Grupo:', g.nombre if g else 'NO ENCONTRADO')

# Lista de emails
emails = [
    'gbarreiroflores@gmail.com',
    'dr.garcia@oncosegunda.com', 
    'dr.lopez@oncosegunda.com',
    'dr.rodriguez@oncosegunda.com'
]

for email in emails:
    try:
        m = Medico.objects.get(usuario__email=email)
        rol = 'coordinador' if email == 'dr.rodriguez@oncosegunda.com' else 'miembro_regular'
        
        # Verificar si ya existe
        existing = DoctorGroupMembership.objects.filter(medico=m, grupo=g).first()
        if existing:
            print(f'Ya existe: {m.nombre_completo}')
            continue
            
        # Crear membresia
        memb = DoctorGroupMembership.objects.create(
            medico=m, 
            grupo=g,
            rol=rol, 
            activo=True, 
            disponible_asignacion_auto=True, 
            es_responsable=(rol == 'coordinador')
        )
        print(f'Asignado: {m.nombre_completo} - {rol}')
    except Medico.DoesNotExist:
        print(f'No encontrado: {email}')

# Actualizar coordinador del grupo
try:
    coordinador = Medico.objects.get(usuario__email='dr.rodriguez@oncosegunda.com')
    g.coordinador = coordinador
    g.save()
    print(f'Coordinador del grupo: {coordinador.nombre_completo}')
except:
    print('No se pudo actualizar el coordinador')

print('Fin')
