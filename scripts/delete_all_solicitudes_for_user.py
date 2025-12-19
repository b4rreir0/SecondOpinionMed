import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
import django
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

EMAIL = 'germanbarreiro2121@gmail.com'

user = User.objects.filter(email__iexact=EMAIL).first()
if not user:
    print('No se encontró usuario con email', EMAIL)
    sys.exit(1)

# Delete cases from app `cases` (Case model)
try:
    from cases.models import Case
except Exception:
    Case = None

deleted_counts = {
    'cases_deleted': 0,
    'solicitudes_deleted': 0,
}

if Case is not None:
    qs = Case.objects.filter(patient=user)
    deleted_counts['cases_deleted'] = qs.count()
    if qs.exists():
        # Use .delete() to cascade
        qs.delete()
        print(f"Eliminados {deleted_counts['cases_deleted']} objetos Case del app 'cases'.")
    else:
        print("No se encontraron Case en app 'cases' para este usuario.")
else:
    print("App 'cases' o modelo Case no disponible en este entorno.")

# Delete SolicitudSegundaOpinion in pacientes app
try:
    from pacientes.models import Paciente, CasoClinico, SolicitudSegundaOpinion
except Exception:
    Paciente = CasoClinico = SolicitudSegundaOpinion = None

# Find Paciente profile (may not exist)
paciente = None
if Paciente is not None:
    paciente = Paciente.objects.filter(usuario=user).first()

# If paciente profile exists, delete SolicitudSegundaOpinion for its casos
if paciente and CasoClinico is not None and SolicitudSegundaOpinion is not None:
    casos = CasoClinico.objects.filter(paciente=paciente)
    count = 0
    for caso in casos:
        try:
            solicitud = caso.solicitud
        except SolicitudSegundaOpinion.DoesNotExist:
            solicitud = None
        if solicitud:
            solicitud.delete()
            count += 1
            print(f'Solicitud eliminada para Caso {caso.uuid}')
    deleted_counts['solicitudes_deleted'] = count
    print(f'Total SolicitudSegundaOpinion eliminadas del app "pacientes": {count}')
else:
    print('Perfil Paciente no encontrado o modelos de pacientes no disponibles; buscando vinculaciones alternativas...')
    # Alternative: buscar SolicitudSegundaOpinion por texto de contacto que contenga email (fallback)
    if SolicitudSegundaOpinion is not None:
        alt_qs = SolicitudSegundaOpinion.objects.filter(medico_remitente__icontains=EMAIL)
        alt_count = alt_qs.count()
        if alt_count:
            deleted_counts['solicitudes_deleted'] = alt_count
            alt_qs.delete()
            print(f'Eliminadas {alt_count} solicitudes donde medico_remitente contenía el email.')

print('Resumen:', deleted_counts)
