# oncosegunda/management/commands/create_initial_data.py
"""
Comando para crear datos iniciales del sistema.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import ModuloSistema, AlgoritmoConfig
from administracion.models import ConfiguracionSistema


class Command(BaseCommand):
    help = 'Crear datos iniciales del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos iniciales...')

        # Crear módulos del sistema
        modulos_data = [
            {
                'nombre': 'Módulo Público',
                'codigo': 'public',
                'descripcion': 'Módulo de páginas públicas y autenticación',
                'version': '1.0.0',
                'estado': 'activo'
            },
            {
                'nombre': 'Módulo Pacientes',
                'codigo': 'pacientes',
                'descripcion': 'Módulo de gestión de pacientes',
                'version': '1.0.0',
                'estado': 'activo'
            },
            {
                'nombre': 'Módulo Médicos',
                'codigo': 'medicos',
                'descripcion': 'Módulo de gestión de médicos',
                'version': '1.0.0',
                'estado': 'activo'
            },
            {
                'nombre': 'Módulo Administración',
                'codigo': 'administracion',
                'descripcion': 'Módulo de administración del sistema',
                'version': '1.0.0',
                'estado': 'activo'
            }
        ]

        for modulo_data in modulos_data:
            modulo, created = ModuloSistema.objects.get_or_create(
                codigo=modulo_data['codigo'],
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
            nombre='Round Robin',
            tipo='asignacion',
            defaults={
                'descripcion': 'Algoritmo de asignación round-robin para distribuir casos equitativamente',
                'configuracion': {
                    'prioridad_especialidad': True,
                    'balanceo_carga': True,
                    'max_casos_simultaneos': 10
                },
                'activo': True
            }
        )
        if created:
            self.stdout.write('  ✓ Algoritmo de asignación creado')
        else:
            self.stdout.write('  - Algoritmo de asignación ya existe')

        # Crear usuario administrador si no existe
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@oncosegunda.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema'
            )
            self.stdout.write('  ✓ Usuario administrador creado (admin/admin123)')
        else:
            self.stdout.write('  - Usuario administrador ya existe')

        self.stdout.write(self.style.SUCCESS('Datos iniciales creados exitosamente'))