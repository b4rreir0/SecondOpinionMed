# core/context_processors.py
from core.models import ModuloSistema, ConfiguracionSistema
from pacientes.models import CasoClinico
from medicos.models import Medico
from administracion.models import NotificacionSistema

def modulos_sistema(request):
    """Context processor que añade información de módulos del sistema"""
    context = {}
    
    if request.user.is_authenticated:
        # Obtener módulos activos
        modulos = ModuloSistema.objects.filter(activa=True)
        context['modulos_sistema'] = modulos
        
        # Información específica por rol
        if hasattr(request.user, 'paciente'):
            paciente = request.user.paciente
            context.update({
                'rol_usuario': 'paciente',
                'paciente_activo': paciente.activo,
                'casos_paciente': CasoClinico.objects.filter(paciente=paciente).count(),
                'casos_activos_paciente': CasoClinico.objects.filter(
                    paciente=paciente, 
                    estado__in=['enviado', 'asignado', 'en_revision', 'comite']
                ).count(),
            })
            
        elif hasattr(request.user, 'medico'):
            medico = request.user.medico
            context.update({
                'rol_usuario': 'medico',
                'medico_activo': medico.estado == 'activo',
                'casos_asignados': CasoClinico.objects.filter(
                    medico_asignado=medico,
                    estado__in=['asignado', 'en_revision']
                ).count(),
                'revisiones_pendientes': CasoClinico.objects.filter(
                    medico_asignado=medico,
                    estado='asignado'
                ).count(),
                'capacidad_disponible': medico.capacidad_disponible,
            })
            
        elif hasattr(request.user, 'administrador'):
            admin = request.user.administrador
            context.update({
                'rol_usuario': 'admin',
                'admin_activo': admin.estado == 'activo',
                'total_casos_sistema': CasoClinico.objects.count(),
                'casos_pendientes': CasoClinico.objects.filter(
                    estado__in=['enviado', 'asignado']
                ).count(),
                'medicos_activos': Medico.objects.filter(estado='activo').count(),
            })
    
    return context

def configuracion_sistema(request):
    """Context processor con configuraciones globales del sistema"""
    context = {}
    
    try:
        # Configuraciones importantes para templates
        configs = ConfiguracionSistema.objects.filter(
            clave__in=[
                'nombre_sistema',
                'version_sistema', 
                'email_contacto',
                'telefono_contacto',
                'modo_mantenimiento'
            ]
        )
        
        for config in configs:
            context[config.clave] = config.valor
            
    except Exception:
        # Valores por defecto si hay error
        context.update({
            'nombre_sistema': 'Sistema de Segundas Opiniones Oncológicas',
            'version_sistema': '1.0.0',
            'email_contacto': 'contacto@oncosegunda.com',
            'telefono_contacto': '+57 1 123 4567',
            'modo_mantenimiento': 'false'
        })
    
    return context

def notificaciones_usuario(request):
    """Context processor para notificaciones del usuario"""
    context = {}
    
    if request.user.is_authenticated:
        # Notificaciones no leídas
        notificaciones = NotificacionSistema.objects.filter(
            destinatarios=request.user,
            leida=False
        ).order_by('-fecha_creacion')[:5]  # Últimas 5
        
        context['notificaciones_no_leidas'] = notificaciones
        context['total_notificaciones'] = notificaciones.count()
        
        # Notificaciones críticas
        notificaciones_criticas = notificaciones.filter(prioridad='critica')
        context['notificaciones_criticas'] = notificaciones_criticas.count()
    
    return context

def estadisticas_generales(request):
    """Context processor con estadísticas generales del sistema"""
    context = {}
    
    if request.user.is_authenticated and hasattr(request.user, 'administrador'):
        from django.db.models import Count, Q
        from django.utils import timezone
        import datetime
        
        # Estadísticas de los últimos 30 días
        hace_30_dias = timezone.now() - datetime.timedelta(days=30)
        
        context.update({
            'casos_ultimo_mes': CasoClinico.objects.filter(
                creado_en__gte=hace_30_dias
            ).count(),
            'casos_concluidos_mes': CasoClinico.objects.filter(
                fecha_conclusion__gte=hace_30_dias,
                estado='concluido'
            ).count(),
            'medicos_disponibles': Medico.objects.filter(
                estado='activo',
                disponible_segundas_opiniones=True
            ).count(),
            'casos_sin_asignar': CasoClinico.objects.filter(
                estado='enviado',
                medico_asignado__isnull=True
            ).count(),
        })
    
    return context