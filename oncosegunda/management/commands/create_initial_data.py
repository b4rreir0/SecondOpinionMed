# oncosegunda/management/commands/create_initial_data.py
"""
Comando para crear datos iniciales del sistema.
Incluye: especialidades, tipos de cáncer, médicos de prueba, comités MDT.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from core.models import ModuloSistema, AlgoritmoConfig
from administracion.models import ConfiguracionSistema
from apps.medicos.models import Especialidad, TipoCancer, Medico, MedicalGroup, DoctorGroupMembership


class Command(BaseCommand):
    help = 'Crear datos iniciales del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos iniciales...')

        # Crear módulos del sistema
        modulos_data = [
            {
                'nombre': 'Módulo Público',
                'descripcion': 'Módulo de páginas públicas y autenticación',
                'version': '1.0.0',
                'estado': 'activo'
            },
            {
                'nombre': 'Módulo Pacientes',
                'descripcion': 'Módulo de gestión de pacientes',
                'version': '1.0.0',
                'estado': 'activo'
            },
            {
                'nombre': 'Módulo Médicos',
                'descripcion': 'Módulo de gestión de médicos',
                'version': '1.0.0',
                'estado': 'activo'
            },
            {
                'nombre': 'Módulo Administración',
                'descripcion': 'Módulo de administración del sistema',
                'version': '1.0.0',
                'estado': 'activo'
            }
        ]

        for modulo_data in modulos_data:
            modulo, created = ModuloSistema.objects.get_or_create(
                nombre=modulo_data['nombre'],
                defaults=modulo_data
            )
            if created:
                self.stdout.write(f'  ✓ Módulo {modulo.nombre} creado')
            else:
                self.stdout.write(f'  - Módulo {modulo.nombre} ya existe')

        # Crear configuraciones del sistema
        configs_data = [
            {
                'clave': 'max_casos_por_medico',
                'valor': '10',
                'tipo': 'int',
                'descripcion': 'Máximo número de casos simultáneos por médico'
            },
            {
                'clave': 'dias_maximo_sin_actualizacion',
                'valor': '30',
                'tipo': 'int',
                'descripcion': 'Días máximos sin actualización antes de alerta'
            },
            {
                'clave': 'email_notificaciones_activo',
                'valor': 'true',
                'tipo': 'bool',
                'descripcion': 'Habilitar envío de notificaciones por email'
            },
            {
                'clave': 'tamano_maximo_archivo_mb',
                'valor': '50',
                'tipo': 'int',
                'descripcion': 'Tamaño máximo de archivo en MB'
            },
            {
                'clave': 'tiempo_expiracion_sesion_minutos',
                'valor': '480',
                'tipo': 'int',
                'descripcion': 'Tiempo de expiración de sesión en minutos'
            }
        ]

        for config_data in configs_data:
            config, created = ConfiguracionSistema.objects.get_or_create(
                clave=config_data['clave'],
                defaults=config_data
            )
            if created:
                self.stdout.write(f'  ✓ Configuración {config.clave} creada')
            else:
                self.stdout.write(f'  - Configuración {config.clave} ya existe')

        # Crear algoritmo de asignación por defecto
        algoritmo, created = AlgoritmoConfig.objects.get_or_create(
            nombre='configuracion_default',
            tipo='asignacion',
            defaults={
                'configuracion': {
                    'ponderacion_carga': 50,
                    'modo_estricto': False,
                    'limite_mensual': 15,
                    'permitir_overrides': True,
                    'respectar_disponibilidad': True
                },
                'activo': True
            }
        )
        if created:
            self.stdout.write('  ✓ Algoritmo de asignación creado')
        else:
            self.stdout.write('  - Algoritmo de asignación ya existe')

        # =========================================
        # CREAR ESPECIALIDADES MÉDICAS
        # =========================================
        self.stdout.write('\nCreando especialidades médicas...')
        especialidades_data = [
            {'nombre': 'Oncología', 'descripcion': 'Especialidad en tratamiento del cáncer'},
            {'nombre': 'Oncología Clínica', 'descripcion': 'Tratamiento médico del cáncer'},
            {'nombre': 'Oncología Quirúrgica', 'descripcion': 'Cirugía oncológica'},
            {'nombre': 'Radioterapia', 'descripcion': 'Tratamiento con radiación'},
            {'nombre': 'Medicina Nuclear', 'descripcion': 'Diagnóstico y tratamiento con isótopos'},
            {'nombre': 'Patología', 'descripcion': 'Estudio de enfermedades por laboratorio'},
            {'nombre': 'Radiología', 'descripcion': 'Diagnóstico por imágenes'},
            {'nombre': 'Cirugía General', 'descripcion': 'Cirugía general y digestiva'},
            {'nombre': 'Neumología', 'descripcion': 'Enfermedades respiratorias'},
            {'nombre': 'Gastroenterología', 'descripcion': 'Enfermedades digestivas'},
        ]
        
        especialidades = {}
        for esp_data in especialidades_data:
            esp, created = Especialidad.objects.get_or_create(
                nombre=esp_data['nombre'],
                defaults={'descripcion': esp_data['descripcion'], 'activa': True}
            )
            especialidades[esp_data['nombre']] = esp
            if created:
                self.stdout.write(f'  ✓ Especialidad: {esp.nombre}')

        # =========================================
        # CREAR TIPOS DE CÁNCER
        # =========================================
        self.stdout.write('\nCreando tipos de cáncer...')
        tipos_cancer_data = [
            {'nombre': 'Cáncer de Pulmón', 'codigo': 'PULMON', 'especialidad': 'Oncología'},
            {'nombre': 'Cáncer de Mama', 'codigo': 'MAMA', 'especialidad': 'Oncología'},
            {'nombre': 'Cáncer Colorrectal', 'codigo': 'COLON', 'especialidad': 'Gastroenterología'},
            {'nombre': 'Cáncer de Próstata', 'codigo': 'PROSTATA', 'especialidad': 'Oncología'},
            {'nombre': 'Cáncer de Hígado', 'codigo': 'HIGADO', 'especialidad': 'Oncología'},
            {'nombre': 'Cáncer de Páncreas', 'codigo': 'PANCREAS', 'especialidad': 'Oncología'},
            {'nombre': 'Cáncer Gástrico', 'codigo': 'GASTRICO', 'especialidad': 'Gastroenterología'},
            {'nombre': 'Cáncer de Tiroides', 'codigo': 'TIROIDES', 'especialidad': 'Oncología'},
            {'nombre': 'Cáncer de Riñón', 'codigo': 'RINON', 'especialidad': 'Oncología'},
            {'nombre': 'Cáncer de Vejiga', 'codigo': 'VEJIGA', 'especialidad': 'Oncología'},
        ]
        
        tipos_cancer = {}
        for tc_data in tipos_cancer_data:
            esp = especialidades.get(tc_data['especialidad'])
            tc, created = TipoCancer.objects.get_or_create(
                codigo=tc_data['codigo'],
                defaults={
                    'nombre': tc_data['nombre'],
                    'especialidad_principal': esp,
                    'activo': True
                }
            )
            tipos_cancer[tc_data['codigo']] = tc
            if created:
                self.stdout.write(f'  ✓ Tipo cáncer: {tc.nombre}')

        # =========================================
        # CREAR USUARIOS Y MÉDICOS DE PRUEBA
        # =========================================
        self.stdout.write('\nCreando médicos de prueba...')
        User = get_user_model()
        
        medicos_data = [
            {
                'username': 'dr.garcia',
                'email': 'dr.garcia@oncosegunda.com',
                'password': 'doctor123',
                'first_name': 'Carlos',
                'last_name': 'García López',
                'tipo_documento': 'cc',
                'numero_documento': '12345678',
                'fecha_nacimiento': '1975-05-15',
                'genero': 'masculino',
                'registro_medico': 'RM-001',
                'experiencia_anios': 15,
                'institucion_actual': 'Hospital Central',
                'telefono': '+573001234567',
                'especialidades': ['Oncología', 'Oncología Clínica'],
                'max_casos_mes': 10
            },
            {
                'username': 'dr.martinez',
                'email': 'dr.martinez@oncosegunda.com',
                'password': 'doctor123',
                'first_name': 'María Elena',
                'last_name': 'Martínez Sánchez',
                'tipo_documento': 'cc',
                'numero_documento': '23456789',
                'fecha_nacimiento': '1980-08-22',
                'genero': 'femenino',
                'registro_medico': 'RM-002',
                'experiencia_anios': 12,
                'institucion_actual': 'Instituto Nacional de Cancerología',
                'telefono': '+573001234568',
                'especialidades': ['Oncología', 'Oncología Quirúrgica'],
                'max_casos_mes': 8
            },
            {
                'username': 'dr.rodriguez',
                'email': 'dr.rodriguez@oncosegunda.com',
                'password': 'doctor123',
                'first_name': 'José Antonio',
                'last_name': 'Rodríguez Pérez',
                'tipo_documento': 'cc',
                'numero_documento': '34567890',
                'fecha_nacimiento': '1972-03-10',
                'genero': 'masculino',
                'registro_medico': 'RM-003',
                'experiencia_anios': 20,
                'institucion_actual': 'Hospital Universitario',
                'telefono': '+573001234569',
                'especialidades': ['Oncología', 'Radioterapia'],
                'max_casos_mes': 12
            },
            {
                'username': 'dr.lopez',
                'email': 'dr.lopez@oncosegunda.com',
                'password': 'doctor123',
                'first_name': 'Ana Patricia',
                'last_name': 'López González',
                'tipo_documento': 'cc',
                'numero_documento': '45678901',
                'fecha_nacimiento': '1985-11-30',
                'genero': 'femenino',
                'registro_medico': 'RM-004',
                'experiencia_anios': 8,
                'institucion_actual': 'Centro de Cancerología',
                'telefono': '+573001234570',
                'especialidades': ['Oncología', 'Medicina Nuclear'],
                'max_casos_mes': 6
            },
            {
                'username': 'dr.hernandez',
                'email': 'dr.hernandez@oncosegunda.com',
                'password': 'doctor123',
                'first_name': 'Roberto',
                'last_name': 'Hernández Díaz',
                'tipo_documento': 'cc',
                'numero_documento': '56789012',
                'fecha_nacimiento': '1978-07-18',
                'genero': 'masculino',
                'registro_medico': 'RM-005',
                'experiencia_anios': 18,
                'institucion_actual': 'Hospital Central',
                'telefono': '+573001234571',
                'especialidades': ['Cirugía General', 'Oncología Quirúrgica'],
                'max_casos_mes': 10
            },
            {
                'username': 'dr.sanchez',
                'email': 'dr.sanchez@oncosegunda.com',
                'password': 'doctor123',
                'first_name': 'Laura Cristina',
                'last_name': 'Sánchez Torres',
                'tipo_documento': 'cc',
                'numero_documento': '67890123',
                'fecha_nacimiento': '1982-01-25',
                'genero': 'femenino',
                'registro_medico': 'RM-006',
                'experiencia_anios': 10,
                'institucion_actual': 'Instituto Nacional de Cancerología',
                'telefono': '+573001234572',
                'especialidades': ['Patología', 'Oncología'],
                'max_casos_mes': 15
            },
        ]
        
        medicos = []
        for med_data in medicos_data:
            # Crear usuario
            usuario, created = User.objects.get_or_create(
                username=med_data['username'],
                defaults={
                    'email': med_data['email'],
                    'first_name': med_data['first_name'],
                    'last_name': med_data['last_name'],
                    'role': 'doctor',
                    'is_active': True
                }
            )
            if created:
                usuario.set_password(med_data['password'])
                usuario.save()
                self.stdout.write(f'  ✓ Usuario creado: {usuario.username} ({med_data["password"]})')
            else:
                self.stdout.write(f'  - Usuario ya existe: {usuario.username}')
            
            # Crear perfil de médico
            from datetime import date
            fecha_nac = date.fromisoformat(med_data['fecha_nacimiento'])
            
            medico, created = Medico.objects.get_or_create(
                usuario=usuario,
                defaults={
                    'tipo_documento': med_data['tipo_documento'],
                    'numero_documento': med_data['numero_documento'],
                    'nombres': med_data['first_name'],
                    'apellidos': med_data['last_name'],
                    'fecha_nacimiento': fecha_nac,
                    'genero': med_data['genero'],
                    'registro_medico': med_data['registro_medico'],
                    'experiencia_anios': med_data['experiencia_anios'],
                    'institucion_actual': med_data['institucion_actual'],
                    'telefono': med_data['telefono'],
                    'max_casos_mes': med_data['max_casos_mes'],
                    'estado': 'activo',
                    'disponible_segundas_opiniones': True
                }
            )
            
            # Agregar especialidades
            for esp_nombre in med_data['especialidades']:
                esp = especialidades.get(esp_nombre)
                if esp:
                    medico.especialidades.add(esp)
            
            medicos.append(medico)
            if created:
                self.stdout.write(f'  ✓ Médico creado: Dr. {medico.nombre_completo}')

        # =========================================
        # CREAR COMITÉS MDT (GRUPOS MÉDICOS)
        # =========================================
        self.stdout.write('\nCreando comités MDT (grupos médicos)...')
        
        grupos_data = [
            {
                'nombre': 'Comité de Tumores Pulmonares',
                'tipo_cancer': 'PULMON',
                'descripcion': 'Comité multidisciplinario para cáncer de pulm\u00f3n',
                'quorum': 3,
                'responsable': 0  # Índice del médico responsable
            },
            {
                'nombre': 'Comité de Tumores Mamarios',
                'tipo_cancer': 'MAMA',
                'descripcion': 'Comité multidisciplinario para cáncer de mama',
                'quorum': 3,
                'responsable': 1
            },
            {
                'nombre': 'Comité de Tumores Digestivos',
                'tipo_cancer': 'COLON',
                'descripcion': 'Comité multidisciplinario para cáncer colorrectal y gástrico',
                'quorum': 4,
                'responsable': 2
            },
            {
                'nombre': 'Comité de Tumores Genitourinarios',
                'tipo_cancer': 'PROSTATA',
                'descripcion': 'Comité multidisciplinario para cáncer de pr\u00f3stata y vejiga',
                'quorum': 3,
                'responsable': 4
            },
        ]
        
        grupos = []
        for i, grp_data in enumerate(grupos_data):
            tc = tipos_cancer.get(grp_data['tipo_cancer'])
            responsable = medicos[grp_data['responsable']] if grp_data['responsable'] < len(medicos) else medicos[0]
            
            grupo, created = MedicalGroup.objects.get_or_create(
                nombre=grp_data['nombre'],
                defaults={
                    'tipo_cancer': tc,
                    'descripcion': grp_data['descripcion'],
                    'quorum_config': grp_data['quorum'],
                    'responsable_por_defecto': responsable,
                    'activo': True
                }
            )
            grupos.append(grupo)
            if created:
                self.stdout.write(f'  ✓ Grupo creado: {grupo.nombre}')

        # =========================================
        # CREAR MEMBRESÍAS DE MÉDICOS EN GRUPOS
        # =========================================
        self.stdout.write('\nCreando membresías de médicos en grupos...')
        
        # Asignar médicos a grupos (cada médico a 1-2 grupos)
        membresias_data = [
            # Comité Pulmonar
            {'medico_idx': 0, 'grupo_idx': 0, 'rol': 'coordinador', 'es_responsable': True},
            {'medico_idx': 2, 'grupo_idx': 0, 'rol': 'miembro_senior', 'es_responsable': False},
            {'medico_idx': 3, 'grupo_idx': 0, 'rol': 'miembro_regular', 'es_responsable': False},
            # Comité Mama
            {'medico_idx': 1, 'grupo_idx': 1, 'rol': 'coordinador', 'es_responsable': True},
            {'medico_idx': 4, 'grupo_idx': 1, 'rol': 'miembro_senior', 'es_responsable': False},
            {'medico_idx': 5, 'grupo_idx': 1, 'rol': 'miembro_regular', 'es_responsable': False},
            # Comité Digestivo
            {'medico_idx': 2, 'grupo_idx': 2, 'rol': 'coordinador', 'es_responsable': True},
            {'medico_idx': 4, 'grupo_idx': 2, 'rol': 'miembro_senior', 'es_responsable': False},
            {'medico_idx': 5, 'grupo_idx': 2, 'rol': 'miembro_regular', 'es_responsable': False},
            # Comité Genitourinario
            {'medico_idx': 4, 'grupo_idx': 3, 'rol': 'coordinador', 'es_responsable': True},
            {'medico_idx': 0, 'grupo_idx': 3, 'rol': 'miembro_regular', 'es_responsable': False},
            {'medico_idx': 1, 'grupo_idx': 3, 'rol': 'miembro_regular', 'es_responsable': False},
        ]
        
        for mem_data in membresias_data:
            medico = medicos[mem_data['medico_idx']]
            grupo = grupos[mem_data['grupo_idx']]
            
            membresia, created = DoctorGroupMembership.objects.get_or_create(
                medico=medico,
                grupo=grupo,
                defaults={
                    'rol': mem_data['rol'],
                    'es_responsable': mem_data['es_responsable']
                }
            )
            if created:
                self.stdout.write(f'  ✓ {medico.nombre_completo} -> {grupo.nombre} ({mem_data["rol"]})')

        # =========================================
        # CREAR USUARIO ADMINISTRADOR
        # =========================================
        self.stdout.write('\nCreando usuario administrador...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@oncosegunda.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema'
            )
            self.stdout.write('  ✓ Usuario administrador creado (admin / admin123)')
        else:
            self.stdout.write('  - Usuario administrador ya existe')

        # =========================================
        # RESUMEN FINAL
        # =========================================
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('DATOS INICIALES CREADOS EXITOSAMENTE'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write('\nCREDENCIALES DE ACCESO:')
        self.stdout.write(self.style.WARNING('  Administrador:'))
        self.stdout.write(self.style.WARNING('    Username: admin'))
        self.stdout.write(self.style.WARNING('    Password: admin123'))
        self.stdout.write(self.style.WARNING('    URL: /admin/'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('  Médicos de prueba:'))
        for i, med in enumerate(medicos):
            password = medicos_data[i]['password']
            self.stdout.write(f'    - {med.usuario.username} / {password} (Dr. {med.nombre_completo})')
        self.stdout.write('')
        self.stdout.write(f'  Especialidades: {len(especialidades)}')
        self.stdout.write(f'  Tipos de cáncer: {len(tipos_cancer)}')
        self.stdout.write(f'  Grupos MDT: {len(grupos)}')
        self.stdout.write('\nPara ejecutar: python manage.py create_initial_data')