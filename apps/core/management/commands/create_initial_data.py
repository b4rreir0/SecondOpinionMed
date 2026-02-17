# Script to create initial data for the system
# Run with: python manage.py create_initial_data

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
django.setup()

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date

from core.models import ModuloSistema, AlgoritmoConfig
from administracion.models import ConfiguracionSistema
from medicos.models import Especialidad, TipoCancer, Medico, MedicalGroup, DoctorGroupMembership


class Command(BaseCommand):
    help = 'Create initial data for the system'

    def handle(self, *args, **options):
        self.stdout.write('Creating initial data...')
        
        User = get_user_model()
        
        # Create system modules
        modules = [
            {'nombre': 'Modulo Publico', 'descripcion': 'Public pages and authentication module', 'version': '1.0.0', 'estado': 'activo'},
            {'nombre': 'Modulo Pacientes', 'descripcion': 'Patient management module', 'version': '1.0.0', 'estado': 'activo'},
            {'nombre': 'Modulo Medicos', 'descripcion': 'Doctor management module', 'version': '1.0.0', 'estado': 'activo'},
            {'nombre': 'Modulo Administracion', 'descripcion': 'System administration module', 'version': '1.0.0', 'estado': 'activo'}
        ]
        
        for mod in modules:
            m, created = ModuloSistema.objects.get_or_create(nombre=mod['nombre'], defaults=mod)
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] Module: {mod["nombre"]}')
        
        # Create system configurations
        configs = [
            {'clave': 'max_casos_por_medico', 'valor': '10', 'tipo': 'int', 'descripcion': 'Max simultaneous cases per doctor'},
            {'clave': 'dias_maximo_sin_actualizacion', 'valor': '30', 'tipo': 'int', 'descripcion': 'Max days without update before alert'},
            {'clave': 'email_notificaciones_activo', 'valor': 'true', 'tipo': 'bool', 'descripcion': 'Enable email notifications'},
            {'clave': 'tamano_maximo_archivo_mb', 'valor': '50', 'tipo': 'int', 'descripcion': 'Max file size in MB'},
            {'clave': 'tiempo_expiracion_sesion_minutos', 'valor': '480', 'tipo': 'int', 'descripcion': 'Session expiration time in minutes'}
        ]
        
        for cfg in configs:
            c, created = ConfiguracionSistema.objects.get_or_create(clave=cfg['clave'], defaults=cfg)
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] Config: {cfg["clave"]}')
        
        # Create algorithm config
        alg, created = AlgoritmoConfig.objects.get_or_create(
            nombre='configuracion_default',
            tipo='asignacion',
            defaults={'configuracion': {'ponderacion_carga': 50, 'modo_estricto': False}, 'activo': True}
        )
        status = 'CREATED' if created else 'EXISTS'
        self.stdout.write(f'  [{status}] Algorithm config')

        # Create specialties
        self.stdout.write('\nCreating medical specialties...')
        specialties_data = [
            {'nombre': 'Oncologia', 'descripcion': 'Cancer treatment specialty'},
            {'nombre': 'Oncologia Clinica', 'descripcion': 'Medical cancer treatment'},
            {'nombre': 'Oncologia Quirurgica', 'descripcion': 'Oncological surgery'},
            {'nombre': 'Radioterapia', 'descripcion': 'Radiation treatment'},
            {'nombre': 'Medicina Nuclear', 'descripcion': 'Isotope diagnosis and treatment'},
            {'nombre': 'Patologia', 'descripcion': 'Disease study by laboratory'},
            {'nombre': 'Radiologia', 'descripcion': 'Imaging diagnosis'},
            {'nombre': 'Cirugia General', 'descripcion': 'General and digestive surgery'},
            {'nombre': 'Neumologia', 'descripcion': 'Respiratory diseases'},
            {'nombre': 'Gastroenterologia', 'descripcion': 'Digestive diseases'}
        ]
        
        specialties = {}
        for sp in specialties_data:
            s, created = Especialidad.objects.get_or_create(nombre=sp['nombre'], defaults={'descripcion': sp['descripcion'], 'activa': True})
            specialties[sp['nombre']] = s
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] Specialty: {sp["nombre"]}')

        # Create cancer types
        self.stdout.write('\nCreating cancer types...')
        cancer_types = [
            {'nombre': 'Cancer de Pulmon', 'codigo': 'PULMON', 'especialidad': 'Oncologia'},
            {'nombre': 'Cancer de Mama', 'codigo': 'MAMA', 'especialidad': 'Oncologia'},
            {'nombre': 'Cancer Colorrectal', 'codigo': 'COLON', 'especialidad': 'Gastroenterologia'},
            {'nombre': 'Cancer de Prostata', 'codigo': 'PROSTATA', 'especialidad': 'Oncologia'},
            {'nombre': 'Cancer de Higado', 'codigo': 'HIGADO', 'especialidad': 'Oncologia'},
            {'nombre': 'Cancer de Pancreas', 'codigo': 'PANCREAS', 'especialidad': 'Oncologia'},
            {'nombre': 'Cancer Gastrico', 'codigo': 'GASTRICO', 'especialidad': 'Gastroenterologia'},
            {'nombre': 'Cancer de Tiroides', 'codigo': 'TIROIDES', 'especialidad': 'Oncologia'},
            {'nombre': 'Cancer de Rinon', 'codigo': 'RINON', 'especialidad': 'Oncologia'},
            {'nombre': 'Cancer de Vejiga', 'codigo': 'VEJIGA', 'especialidad': 'Oncologia'}
        ]
        
        tipos_cancer = {}
        for ct in cancer_types:
            esp = specialties.get(ct['especialidad'])
            c, created = TipoCancer.objects.get_or_create(
                codigo=ct['codigo'],
                defaults={'nombre': ct['nombre'], 'especialidad_principal': esp, 'activo': True}
            )
            tipos_cancer[ct['codigo']] = c
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] Cancer type: {ct["nombre"]}')

        # Create test doctors
        self.stdout.write('\nCreating test doctors...')
        doctors_data = [
            {'username': 'dr.garcia', 'email': 'dr.garcia@oncosegunda.com', 'password': 'doctor123', 
             'first_name': 'Carlos', 'last_name': 'Garcia Lopez', 'tipo_documento': 'cc', 'numero_documento': '12345678',
             'fecha_nacimiento': '1975-05-15', 'genero': 'masculino', 'registro_medico': 'RM-001',
             'experiencia_anios': 15, 'institucion_actual': 'Hospital Central', 'telefono': '+573001234567',
             'especialidades': ['Oncologia', 'Oncologia Clinica'], 'max_casos_mes': 10},
            {'username': 'dr.martinez', 'email': 'dr.martinez@oncosegunda.com', 'password': 'doctor123',
             'first_name': 'Maria Elena', 'last_name': 'Martinez Sanchez', 'tipo_documento': 'cc', 'numero_documento': '23456789',
             'fecha_nacimiento': '1980-08-22', 'genero': 'femenino', 'registro_medico': 'RM-002',
             'experiencia_anios': 12, 'institucion_actual': 'Instituto Nacional de Cancerologia', 'telefono': '+573001234568',
             'especialidades': ['Oncologia', 'Oncologia Quirurgica'], 'max_casos_mes': 8},
            {'username': 'dr.rodriguez', 'email': 'dr.rodriguez@oncosegunda.com', 'password': 'doctor123',
             'first_name': 'Jose Antonio', 'last_name': 'Rodriguez Perez', 'tipo_documento': 'cc', 'numero_documento': '34567890',
             'fecha_nacimiento': '1972-03-10', 'genero': 'masculino', 'registro_medico': 'RM-003',
             'experiencia_anios': 20, 'institucion_actual': 'Hospital Universitario', 'telefono': '+573001234569',
             'especialidades': ['Oncologia', 'Radioterapia'], 'max_casos_mes': 12},
            {'username': 'dr.lopez', 'email': 'dr.lopez@oncosegunda.com', 'password': 'doctor123',
             'first_name': 'Ana Patricia', 'last_name': 'Lopez Gonzalez', 'tipo_documento': 'cc', 'numero_documento': '45678901',
             'fecha_nacimiento': '1985-11-30', 'genero': 'femenino', 'registro_medico': 'RM-004',
             'experiencia_anios': 8, 'institucion_actual': 'Centro de Cancerologia', 'telefono': '+573001234570',
             'especialidades': ['Oncologia', 'Medicina Nuclear'], 'max_casos_mes': 6},
            {'username': 'dr.hernandez', 'email': 'dr.hernandez@oncosegunda.com', 'password': 'doctor123',
             'first_name': 'Roberto', 'last_name': 'Hernandez Diaz', 'tipo_documento': 'cc', 'numero_documento': '56789012',
             'fecha_nacimiento': '1978-07-18', 'genero': 'masculino', 'registro_medico': 'RM-005',
             'experiencia_anios': 18, 'institucion_actual': 'Hospital Central', 'telefono': '+573001234571',
             'especialidades': ['Cirugia General', 'Oncologia Quirurgica'], 'max_casos_mes': 10},
            {'username': 'dr.sanchez', 'email': 'dr.sanchez@oncosegunda.com', 'password': 'doctor123',
             'first_name': 'Laura Cristina', 'last_name': 'Sanchez Torres', 'tipo_documento': 'cc', 'numero_documento': '67890123',
             'fecha_nacimiento': '1982-01-25', 'genero': 'femenino', 'registro_medico': 'RM-006',
             'experiencia_anios': 10, 'institucion_actual': 'Instituto Nacional de Cancerologia', 'telefono': '+573001234572',
             'especialidades': ['Patologia', 'Oncologia'], 'max_casos_mes': 15}
        ]
        
        medicos = []
        for doc in doctors_data:
            usuario, created = User.objects.get_or_create(
                username=doc['username'],
                defaults={'email': doc['email'], 'first_name': doc['first_name'], 'last_name': doc['last_name'], 'role': 'doctor', 'is_active': True}
            )
            if created:
                usuario.set_password(doc['password'])
                usuario.save()
            
            fecha_nac = date.fromisoformat(doc['fecha_nacimiento'])
            medico, created = Medico.objects.get_or_create(
                usuario=usuario,
                defaults={
                    'tipo_documento': doc['tipo_documento'], 'numero_documento': doc['numero_documento'],
                    'nombres': doc['first_name'], 'apellidos': doc['last_name'],
                    'fecha_nacimiento': fecha_nac, 'genero': doc['genero'],
                    'registro_medico': doc['registro_medico'], 'experiencia_anios': doc['experiencia_anios'],
                    'institucion_actual': doc['institucion_actual'], 'telefono': doc['telefono'],
                    'max_casos_mes': doc['max_casos_mes'], 'estado': 'activo', 'disponible_segundas_opiniones': True
                }
            )
            
            for esp_nombre in doc['especialidades']:
                esp = specialties.get(esp_nombre)
                if esp:
                    medico.especialidades.add(esp)
            
            medicos.append(medico)
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] Doctor: Dr. {medico.nombre_completo} ({doc["username"]}/{doc["password"]})')

        # Create MDT Committees
        self.stdout.write('\nCreating MDT committees...')
        grupos_data = [
            {'nombre': 'Comite de Tumores Pulmonares', 'tipo_cancer': 'PULMON', 'descripcion': 'Multidisciplinary committee for lung cancer', 'quorum': 3, 'responsable': 0},
            {'nombre': 'Comite de Tumores Mamarios', 'tipo_cancer': 'MAMA', 'descripcion': 'Multidisciplinary committee for breast cancer', 'quorum': 3, 'responsable': 1},
            {'nombre': 'Comite de Tumores Digestivos', 'tipo_cancer': 'COLON', 'descripcion': 'Multidisciplinary committee for colorectal and gastric cancer', 'quorum': 4, 'responsable': 2},
            {'nombre': 'Comite de Tumores Genitourinarios', 'tipo_cancer': 'PROSTATA', 'descripcion': 'Multidisciplinary committee for prostate and bladder cancer', 'quorum': 3, 'responsable': 4}
        ]
        
        grupos = []
        for i, grp in enumerate(grupos_data):
            tc = tipos_cancer.get(grp['tipo_cancer'])
            responsable = medicos[grp['responsable']] if grp['responsable'] < len(medicos) else medicos[0]
            
            grupo, created = MedicalGroup.objects.get_or_create(
                nombre=grp['nombre'],
                defaults={'tipo_cancer': tc, 'descripcion': grp['descripcion'], 'quorum_config': grp['quorum'], 'responsable_por_defecto': responsable, 'activo': True}
            )
            grupos.append(grupo)
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] Committee: {grp["nombre"]}')

        # Create memberships
        self.stdout.write('\nCreating doctor memberships...')
        memberships = [
            {'medico_idx': 0, 'grupo_idx': 0, 'rol': 'coordinador', 'es_responsable': True},
            {'medico_idx': 2, 'grupo_idx': 0, 'rol': 'miembro_senior', 'es_responsable': False},
            {'medico_idx': 3, 'grupo_idx': 0, 'rol': 'miembro_regular', 'es_responsable': False},
            {'medico_idx': 1, 'grupo_idx': 1, 'rol': 'coordinador', 'es_responsable': True},
            {'medico_idx': 4, 'grupo_idx': 1, 'rol': 'miembro_senior', 'es_responsable': False},
            {'medico_idx': 5, 'grupo_idx': 1, 'rol': 'miembro_regular', 'es_responsable': False},
            {'medico_idx': 2, 'grupo_idx': 2, 'rol': 'coordinador', 'es_responsable': True},
            {'medico_idx': 4, 'grupo_idx': 2, 'rol': 'miembro_senior', 'es_responsable': False},
            {'medico_idx': 5, 'grupo_idx': 2, 'rol': 'miembro_regular', 'es_responsable': False},
            {'medico_idx': 4, 'grupo_idx': 3, 'rol': 'coordinador', 'es_responsable': True},
            {'medico_idx': 0, 'grupo_idx': 3, 'rol': 'miembro_regular', 'es_responsable': False},
            {'medico_idx': 1, 'grupo_idx': 3, 'rol': 'miembro_regular', 'es_responsable': False}
        ]
        
        for mem in memberships:
            medico = medicos[mem['medico_idx']]
            grupo = grupos[mem['grupo_idx']]
            membresia, created = DoctorGroupMembership.objects.get_or_create(
                medico=medico, grupo=grupo,
                defaults={'rol': mem['rol'], 'es_responsable': mem['es_responsable']}
            )
            if created:
                self.stdout.write(f'  [+ Membership] Dr. {medico.nombre_completo} -> {grupo.nombre} ({mem["rol"]})')

        # Create admin
        self.stdout.write('\nCreating admin user...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(username='admin', email='admin@oncosegunda.com', password='admin123', first_name='Administrador', last_name='Sistema')
            self.stdout.write('  [CREATED] Admin user (admin/admin123)')
        else:
            self.stdout.write('  [EXISTS] Admin user')

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write('INITIAL DATA CREATED SUCCESSFULLY')
        self.stdout.write('='*60)
        self.stdout.write('\nLOGIN CREDENTIALS:')
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('\nTest Doctors:')
        for i, med in enumerate(medicos):
            pwd = doctors_data[i]['password']
            self.stdout.write(f'  - {med.usuario.username} / {pwd}')
        self.stdout.write(f'\nSpecialties: {len(specialties)}')
        self.stdout.write(f'Cancer Types: {len(tipos_cancer)}')
        self.stdout.write(f'MDT Committees: {len(grupos)}')
