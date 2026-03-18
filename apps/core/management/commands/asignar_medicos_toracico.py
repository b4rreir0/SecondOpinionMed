# Asignar medicos al grupo de Tumores Toracico
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
django.setup()

from medicos.models import Medico, MedicalGroup, DoctorGroupMembership

# Buscar el grupo de Tumores Toracico
try:
    grupo_toracico = MedicalGroup.objects.get(nombre__icontains='Tumores Toracico')
    print(f'Grupo encontrado: {grupo_toracico.nombre}')
except MedicalGroup.DoesNotExist:
    print('ERROR: No se encontro el grupo de Tumores Toracico')
    exit(1)

# Buscar los medicos por email
emails = [
    'agenciarentao@gmail.com',
    'grm4nb4rreir0@gmail.com', 
    'gbarreiroflores@gmail.com',
    'dr.garcia@oncosegunda.com',
    'dr.lopez@oncosegunda.com',
    'dr.rodriguez@oncosegunda.com'  # Coordinador
]

asignados = 0
for email in emails:
    try:
        medico = Medico.objects.get(usuario__email=email)
        # Crear membresia
        membresia, created = DoctorGroupMembership.objects.get_or_create(
            medico=medico,
            grupo=grupo_toracico,
            defaults={
                'rol': 'coordinador' if email == 'dr.rodriguez@oncosegunda.com' else 'miembro_regular',
                'activo': True,
                'disponible_asignacion_auto': True,
                'es_responsable': email == 'dr.rodriguez@oncosegunda.com'
            }
        )
        if created:
            print(f'  [+] {medico.nombre_completo}')
            asignados += 1
        else:
            print(f'  [!] {medico.nombre_completo} (ya existe)')
    except Medico.DoesNotExist:
        print(f'  [X] No encontrado: {email}')

# Actualizar el coordinador del grupo
try:
    coordinador = Medico.objects.get(usuario__email='dr.rodriguez@oncosegunda.com')
    grupo_toracico.coordinador = coordinador
    grupo_toracico.save()
    print(f'\nCoordinador actualizado: {coordinador.nombre_completo}')
except Medico.DoesNotExist:
    print('\nNo se pudo actualizar el coordinador')

print(f'\nTotal asignados: {asignados}')
