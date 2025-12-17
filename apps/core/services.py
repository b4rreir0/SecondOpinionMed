# core/services.py
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from pacientes.models import CasoClinico, Paciente
from medicos.models import Medico, ComiteMultidisciplinario
from core.models import AlgoritmoConfig, Auditoria
import logging
import random

logger = logging.getLogger(__name__)

class AsignacionService:
    """Servicio para asignación automática de casos médicos"""
    
    @staticmethod
    def asignar_caso_medico(caso):
        """Asigna un caso a un médico disponible basado en algoritmos"""
        try:
            # Obtener configuración del algoritmo
            config = AlgoritmoConfig.objects.filter(
                tipo='asignacion',
                activo=True
            ).first()
            
            if not config:
                # Algoritmo por defecto: asignación por especialidad y carga de trabajo
                return AsignacionService._asignacion_por_defecto(caso)
            
            algoritmo = config.configuracion.get('algoritmo', 'default')
            
            if algoritmo == 'especialidad_balanceada':
                return AsignacionService._asignacion_especialidad_balanceada(caso)
            elif algoritmo == 'carga_trabajo':
                return AsignacionService._asignacion_por_carga(caso)
            else:
                return AsignacionService._asignacion_por_defecto(caso)
                
        except Exception as e:
            logger.error(f"Error en asignación de caso {caso.uuid}: {str(e)}")
            return None
    
    @staticmethod
    def _asignacion_por_defecto(caso):
        """Asignación por defecto: médico disponible con especialidad coincidente"""
        # Buscar médicos disponibles con especialidad relacionada
        medicos_disponibles = Medico.objects.filter(
            estado='activo',
            disponible_segundas_opiniones=True,
            especialidades__in=caso.especialidad_solicitada.all() if hasattr(caso, 'especialidad_solicitada') else []
        ).distinct()
        
        if medicos_disponibles.exists():
            # Seleccionar médico con menor carga actual
            medico = medicos_disponibles.order_by('casos_actuales').first()
            caso.asignar_medico(medico)
            return medico
        
        return None
    
    @staticmethod
    def _asignacion_especialidad_balanceada(caso):
        """Asignación balanceada por especialidad y experiencia"""
        medicos_disponibles = Medico.objects.filter(
            estado='activo',
            disponible_segundas_opiniones=True
        ).order_by('casos_actuales', '-experiencia_anios')
        
        for medico in medicos_disponibles:
            if medico.capacidad_disponible > 0:
                caso.asignar_medico(medico)
                return medico
        
        return None
    
    @staticmethod
    def _asignacion_por_carga(caso):
        """Asignación basada únicamente en carga de trabajo"""
        medico = Medico.objects.filter(
            estado='activo',
            disponible_segundas_opiniones=True,
            casos_actuales__lt=models.F('max_casos_mes')
        ).order_by('casos_actuales').first()
        
        if medico:
            caso.asignar_medico(medico)
            return medico
        
        return None

class NotificacionService:
    """Servicio para envío de notificaciones"""
    
    @staticmethod
    def notificar_asignacion_caso(caso, medico):
        """Notifica a un médico sobre asignación de caso"""
        try:
            subject = f'Nuevo caso asignado: {caso.titulo}'
            context = {
                'medico': medico,
                'caso': caso,
                'paciente': caso.paciente,
            }
            
            html_message = render_to_string('emails/caso_asignado.html', context)
            plain_message = render_to_string('emails/caso_asignado.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[medico.usuario.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Notificación enviada a {medico.usuario.email} por caso {caso.uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando notificación de caso asignado: {str(e)}")
            return False
    
    @staticmethod
    def notificar_paciente_actualizacion(caso):
        """Notifica al paciente sobre actualización de su caso"""
        try:
            subject = f'Actualización de su caso: {caso.titulo}'
            context = {
                'caso': caso,
                'paciente': caso.paciente,
            }
            
            html_message = render_to_string('emails/caso_actualizado.html', context)
            plain_message = render_to_string('emails/caso_actualizado.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[caso.paciente.usuario.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando notificación al paciente: {str(e)}")
            return False

class ComiteService:
    """Servicio para gestión de comités multidisciplinarios"""
    
    @staticmethod
    def asignar_a_comite(caso):
        """Asigna un caso a un comité multidisciplinario"""
        try:
            # Buscar comité disponible con especialidades requeridas
            comites_disponibles = ComiteMultidisciplinario.objects.filter(
                activo=True,
                casos_actuales__lt=models.F('max_casos_simultaneos')
            )
            
            for comite in comites_disponibles:
                if comite.puede_asignar_caso():
                    caso.enviar_a_comite(comite)
                    comite.casos_actuales += 1
                    comite.save()
                    
                    # Notificar a miembros del comité
                    NotificacionService.notificar_comite_nuevo_caso(comite, caso)
                    return comite
            
            return None
            
        except Exception as e:
            logger.error(f"Error asignando caso a comité: {str(e)}")
            return None
    
    @staticmethod
    def programar_reunion_comite(comite, caso, fecha):
        """Programa una reunión de comité para un caso"""
        from medicos.models import ReunionComite
        
        try:
            with transaction.atomic():
                reunion = ReunionComite.objects.create(
                    comite=comite,
                    caso=caso,
                    fecha_programada=fecha,
                    moderador=comite.miembros_activos.first()  # Moderador por defecto
                )
                
                # Agregar miembros disponibles
                miembros = comite.miembros_activos[:comite.min_medicos]
                reunion.medicos_participantes.set(miembros)
                
                return reunion
                
        except Exception as e:
            logger.error(f"Error programando reunión de comité: {str(e)}")
            return None

class AuditoriaService:
    """Servicio para registro de auditoría"""
    
    @staticmethod
    def registrar_accion(usuario, tipo_accion, modelo_afectado, objeto_id=None, descripcion="", ip_address=None):
        """Registra una acción en el sistema de auditoría"""
        try:
            Auditoria.objects.create(
                usuario=usuario,
                tipo_accion=tipo_accion,
                modelo_afectado=modelo_afectado,
                objeto_id=objeto_id,
                descripcion=descripcion,
                ip_address=ip_address,
                fecha=timezone.now()
            )
        except Exception as e:
            logger.error(f"Error registrando auditoría: {str(e)}")
    
    @staticmethod
    def registrar_cambio_modelo(instance, usuario, cambios):
        """Registra cambios en un modelo"""
        descripcion = f"Cambios en {instance.__class__.__name__}: {', '.join(cambios)}"
        AuditoriaService.registrar_accion(
            usuario=usuario,
            tipo_accion='modificacion',
            modelo_afectado=instance.__class__.__name__,
            objeto_id=instance.pk,
            descripcion=descripcion
        )

class ReporteService:
    """Servicio para generación de reportes"""
    
    @staticmethod
    def generar_reporte_casos_mes(mes=None, anio=None):
        """Genera reporte de casos del mes"""
        if not mes:
            mes = timezone.now().month
        if not anio:
            anio = timezone.now().year
            
        casos = CasoClinico.objects.filter(
            creado_en__year=anio,
            creado_en__month=mes
        )
        
        estadisticas = {
            'total_casos': casos.count(),
            'casos_concluidos': casos.filter(estado='concluido').count(),
            'casos_pendientes': casos.exclude(estado__in=['concluido', 'cancelado']).count(),
            'tiempo_promedio_resolucion': None,  # Calcular basado en fechas
        }
        
        return estadisticas
    
    @staticmethod
    def generar_reporte_medicos():
        """Genera reporte de actividad de médicos"""
        medicos = Medico.objects.filter(estado='activo')
        
        reporte = []
        for medico in medicos:
            reporte.append({
                'medico': medico.nombre_completo,
                'casos_actuales': medico.casos_actuales,
                'casos_revisados': medico.casos_revisados,
                'capacidad_disponible': medico.capacidad_disponible,
                'calificacion_promedio': medico.calificacion_promedio,
            })
        
        return reporte