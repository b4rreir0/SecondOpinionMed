#!/usr/bin/env python
"""
Script para poblar datos iniciales del sistema de segundas opiniones oncológicas
"""
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from core.models import ModuloSistema, AlgoritmoConfig
from medicos.models import Especialidad
from administracion.models import ConfiguracionSistema

def crear_grupos_permisos():
    """Crear grupos y permisos básicos"""
    print("Creando grupos y permisos...")

    # Grupo Pacientes
    grupo_pacientes, created = Group.objects.get_or_create(name='pacientes')
    if created:
        print("  Grupo 'pacientes' creado")

    # Grupo Médicos
    grupo_medicos, created = Group.objects.get_or_create(name='medicos')
    if created:
        print("  Grupo 'medicos' creado")

    # Grupo Administradores
    grupo_admin, created = Group.objects.get_or_create(name='administradores')
    if created:
        print("  Grupo 'administradores' creado")

def crear_modulos_sistema():
    """Crear módulos del sistema"""
    print("Creando módulos del sistema...")

    modulos = [
        {
            'nombre': 'pacientes',
            'descripcion': 'Módulo de gestión de pacientes',
            'estado': 'activo',
            'version': '1.0',
        },
        {
            'nombre': 'medicos',
            'descripcion': 'Módulo de gestión de médicos especialistas',
            'estado': 'activo',
            'version': '1.0',
        },
        {
            'nombre': 'administracion',
            'descripcion': 'Módulo de administración del sistema',
            'estado': 'activo',
            'version': '1.0',
        },
        {
            'nombre': 'segundas_opiniones',
            'descripcion': 'Módulo de segundas opiniones médicas',
            'estado': 'activo',
            'version': '1.0',
        },
        {
            'nombre': 'comites',
            'descripcion': 'Módulo de comités multidisciplinarios',
            'estado': 'activo',
            'version': '1.0',
        },
    ]

    for modulo_data in modulos:
        modulo, created = ModuloSistema.objects.get_or_create(
            nombre=modulo_data['nombre'],
            defaults=modulo_data
        )
        if created:
            print(f"  Módulo '{modulo.nombre}' creado")

def crear_especialidades():
    """Crear especialidades médicas"""
    print("Creando especialidades médicas...")

    especialidades = [
        {'nombre': 'Oncología Médica', 'descripcion': 'Especialidad en tratamiento médico del cáncer'},
        {'nombre': 'Oncología Quirúrgica', 'descripcion': 'Especialidad en cirugía oncológica'},
        {'nombre': 'Oncología Radioterápica', 'descripcion': 'Especialidad en radioterapia'},
        {'nombre': 'Patología', 'descripcion': 'Especialidad en diagnóstico anatomopatológico'},
        {'nombre': 'Radiología', 'descripcion': 'Especialidad en diagnóstico por imágenes'},
        {'nombre': 'Medicina Interna', 'descripcion': 'Especialidad en medicina interna'},
        {'nombre': 'Hematología', 'descripcion': 'Especialidad en enfermedades de la sangre'},
        {'nombre': 'Ginecología Oncológica', 'descripcion': 'Especialidad en cáncer ginecológico'},
        {'nombre': 'Urología Oncológica', 'descripcion': 'Especialidad en cáncer urológico'},
        {'nombre': 'Neumología', 'descripcion': 'Especialidad en enfermedades respiratorias'},
        {'nombre': 'Gastroenterología', 'descripcion': 'Especialidad en enfermedades digestivas'},
        {'nombre': 'Dermatología', 'descripcion': 'Especialidad en enfermedades de la piel'},
    ]

    for esp_data in especialidades:
        especialidad, created = Especialidad.objects.get_or_create(
            nombre=esp_data['nombre'],
            defaults=esp_data
        )
        if created:
            print(f"  Especialidad '{especialidad.nombre}' creada")

def crear_configuraciones_sistema():
    """Crear configuraciones básicas del sistema"""
    print("Creando configuraciones del sistema...")

    configuraciones = [
        {
            'clave': 'nombre_sistema',
            'valor': 'Sistema de Segundas Opiniones Oncológicas',
            'tipo': 'general',
            'descripcion': 'Nombre del sistema',
        },
        {
            'clave': 'version_sistema',
            'valor': '1.0.0',
            'tipo': 'general',
            'descripcion': 'Versión actual del sistema',
        },
        {
            'clave': 'email_contacto',
            'valor': 'contacto@oncosegunda.com',
            'tipo': 'general',
            'descripcion': 'Email de contacto del sistema',
        },
        {
            'clave': 'telefono_contacto',
            'valor': '+57 1 123 4567',
            'tipo': 'general',
            'descripcion': 'Teléfono de contacto del sistema',
        },
        {
            'clave': 'modo_mantenimiento',
            'valor': 'false',
            'tipo': 'general',
            'descripcion': 'Indica si el sistema está en modo mantenimiento',
        },
        {
            'clave': 'max_casos_por_medico',
            'valor': '10',
            'tipo': 'algoritmos',
            'descripcion': 'Máximo número de casos por médico al mes',
        },
        {
            'clave': 'dias_notificacion_recordatorio',
            'valor': '7',
            'tipo': 'notificaciones',
            'descripcion': 'Días antes para enviar recordatorios',
        },
    ]

    for config_data in configuraciones:
        config, created = ConfiguracionSistema.objects.get_or_create(
            clave=config_data['clave'],
            defaults=config_data
        )
        if created:
            print(f"  Configuración '{config.clave}' creada")

def crear_algoritmos_config():
    """Crear configuraciones de algoritmos"""
    print("Creando configuraciones de algoritmos...")

    algoritmos = [
        {
            'nombre': 'asignacion_basica',
            'tipo': 'asignacion',
            'configuracion': {
                'algoritmo': 'especialidad_balanceada',
                'priorizar_experiencia': True,
                'max_carga_trabajo': 10,
            },
            'activo': True,
        },
        {
            'nombre': 'notificaciones_basicas',
            'tipo': 'notificaciones',
            'configuracion': {
                'email_habilitado': True,
                'sms_habilitado': False,
                'recordatorios_habilitados': True,
            },
            'activo': True,
        },
    ]

    for alg_data in algoritmos:
        algoritmo, created = AlgoritmoConfig.objects.get_or_create(
            nombre=alg_data['nombre'],
            tipo=alg_data['tipo'],
            defaults=alg_data
        )
        if created:
            print(f"  Algoritmo '{algoritmo.nombre}' creado")

def main():
    """Función principal"""
    print("Iniciando población de datos iniciales...")
    print("=" * 50)

    try:
        crear_grupos_permisos()
        print()

        crear_modulos_sistema()
        print()

        crear_especialidades()
        print()

        crear_configuraciones_sistema()
        print()

        crear_algoritmos_config()
        print()

        print("¡Datos iniciales poblados exitosamente!")
        print("=" * 50)
        print("Puede iniciar el servidor con: python manage.py runserver")

    except Exception as e:
        print(f"Error durante la población de datos: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()