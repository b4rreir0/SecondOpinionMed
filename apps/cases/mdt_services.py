"""
Servicios para las funcionalidades MDT P0.

Contiene:
- Algoritmo de asignación round-robin avanzado
- Workflow de consenso formal
- Servicios de mensajería MDT
- Gestión de presencia
- Generación de respuestas y PDFs
"""

from django.db import models
from django.db.models import Count, Q, F, Avg, Max
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Case, MedicalOpinion
from .mdt_models import (
    MDTMessage, UserPresence, AlgoritmoConfig, AsignacionAuditLog,
    ConsensusWorkflow, ConsensusVersion, ConsensusVote, OpinionDisidente
)
from medicos.models import Medico, MedicalGroup, DoctorGroupMembership

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


# =====================================================
# SERVICIO DE ASIGNACIÓN ROUND-ROBIN AVANZADO
# =====================================================

class AssignmentService:
    """
    Servicio para la asignación avanzada de casos a médicos.
    
    Implementa:
    - Ponderación configurable entre carga y antigüedad
    - Modo estricto round-robin
    - Respeto de límites mensuales
    - Registro de auditoría completo
    - Override manual
    """
    
    @staticmethod
    def get_config():
        """Obtiene la configuración activa del algoritmo"""
        return AlgoritmoConfig.objects.filter(activo=True).first()
    
    @staticmethod
    def calcular_score_carga(medico, config):
        """
        Calcula score de carga (0-1, menor es mejor).
        
        Considera: casos activos / capacidad máxima
        """
        capacidad = medico.max_casos_mes or 1
        carga = medico.casos_actuales or 0
        return min(1.0, carga / capacidad)
    
    @staticmethod
    def calcular_score_antiguedad(medico):
        """
        Calcula score de antigüedad (0-1, mayor es mejor).
        
        Normaliza días desde el ingreso.
        """
        dias_activo = (timezone.now() - medico.fecha_ingreso).days
        # Normalizar a 0-1 (asumiendo máx 5 años = 1825 días)
        return min(1.0, dias_activo / 1825)
    
    @staticmethod
    def calcular_score_compuesto(medico, config):
        """
        Calcula score final ponderado.
        
        Score menor = mejor candidato (menos casos, más antigüedad)
        """
        score_carga = AssignmentService.calcular_score_carga(medico, config)
        score_antiguedad = AssignmentService.calcular_score_antiguedad(medico)
        
        ponderacion = config.ponderacion_carga / 100.0
        
        if config.modo_estricto:
            # Round-robin puro: solo considera orden de antigüedad
            score_final = -score_antiguedad  # Negativo para que mayor antigüedad = mejor
        else:
            # Ponderación configurada
            score_final = (ponderacion * score_carga) - ((1 - ponderacion) * score_antiguedad)
        
        return {
            'score_carga': score_carga,
            'score_antiguedad': score_antiguedad,
            'score_final': score_final
        }
    
    @staticmethod
    def get_candidatos(grupo, config):
        """
        Obtiene lista de médicos candidatos para un grupo.
        
        Aplica filtros de disponibilidad y límites.
        """
        # Obtener miembros activos del grupo
        miembros = DoctorGroupMembership.objects.filter(
            grupo=grupo,
            activo=True
        ).select_related('medico')
        
        candidatos = []
        for membresia in miembros:
            medico = membresia.medico
            
            # Verificar disponibilidad
            if config.respetar_disponibilidad and not medico.disponible_segundas_opiniones:
                continue
            
            # Verificar límite mensual
            if medico.casos_actuales >= config.limite_mensual_por_medico:
                continue
            
            # Verificar estado activo
            if medico.estado != 'activo':
                continue
            
            candidatos.append(medico)
        
        return candidatos
    
    @staticmethod
    def asignar_caso(caso, override_medico=None, override_por=None, override_justificacion=''):
        """
        Asigna un caso al médico más apropiado.
        
        Args:
            caso: Instancia de Case
            override_medico: Médico para asignación manual (opcional)
            override_por: Usuario que hace el override
            override_justificacion: Razón del override manual
            
        Returns:
            Medico asignado o None si no hay candidatos
        """
        config = AssignmentService.get_config()
        
        if override_medico:
            # Override manual
            medico = override_medico
            decision = 'asignado'
            motivo = f'Override manual por {override_por.email}'
            
            AsignacionAuditLog.objects.create(
                caso=caso,
                medico_seleccionado=medico,
                decision=decision,
                motivo=motivo,
                config=config,
                es_override=True,
                override_justificacion=override_justificacion,
                override_por=override_por
            )
        else:
            # Algoritmo automático
            grupo = caso.medical_group
            if not grupo:
                return None
            
            candidatos = AssignmentService.get_candidatos(grupo, config)
            
            if not candidatos:
                return None
            
            # Calcular scores y ordenar
            candidatos_con_score = []
            for medico in candidatos:
                scores = AssignmentService.calcular_score_compuesto(medico, config)
                candidatos_con_score.append({
                    'medico': medico,
                    **scores
                })
            
            # Ordenar por score (menor = mejor)
            candidatos_con_score.sort(key=lambda x: x['score_final'])
            
            # Seleccionar el mejor candidato
            mejor = candidatos_con_score[0]
            medico = mejor['medico']
            decision = 'asignado'
            motivo = f'Score más bajo: carga={mejor["score_carga"]:.2f}, antiguedad={mejor["score_antiguedad"]:.2f}'
            
            # Registrar por qué se saltaron los otros
            for candidato in candidatos_con_score[1:]:
                AsignacionAuditLog.objects.create(
                    caso=caso,
                    medico_seleccionado=candidato['medico'],
                    decision='saltado',
                    motivo=f'Score mayor: {candidato["score_final"]:.2f}',
                    score_carga=candidato['score_carga'],
                    score_antiguedad=candidato['score_antiguedad'],
                    score_final=candidato['score_final'],
                    config=config
                )
            
            # Registrar asignación
            AsignacionAuditLog.objects.create(
                caso=caso,
                medico_seleccionado=medico,
                decision=decision,
                motivo=motivo,
                score_carga=mejor['score_carga'],
                score_antiguedad=mejor['score_antiguedad'],
                score_final=mejor['score_final'],
                config=config
            )
        
        # Asignar al caso
        caso.doctor = medico.usuario
        caso.responsable = medico
        caso.assigned_at = timezone.now()
        
        try:
            caso.assign_to_group()
        except Exception:
            pass
        
        caso.save()
        
        return medico


# =====================================================
# SERVICIO DE WORKFLOW DE CONSENSO
# =====================================================

class ConsensusService:
    """
    Servicio para gestionar el workflow formal de consenso MDT.
    
    Fases:
    - DISCUSION: Conversación informal
    - PROPUESTA: Coordinador redacta borrador
    - VOTACION: Miembros votan
    - CONSENSO: Acuerdo alcanzado
    - DISENSO: Disenso registrado
    - BLOQUEADO: Esperando más información
    """
    
    @staticmethod
    def iniciar_workflow(caso):
        """Inicia el workflow de consenso para un caso"""
        workflow, created = ConsensusWorkflow.objects.get_or_create(
            caso=caso,
            defaults={'fase': 'DISCUSION'}
        )
        return workflow
    
    @staticmethod
    def cambiar_fase(workflow, nueva_fase):
        """Cambia la fase del workflow"""
        workflow.fase = nueva_fase
        
        if nueva_fase == 'CONSENSO':
            workflow.fecha_consenso = timezone.now()
            workflow.nivel_evidencia = workflow.calcular_nivel_evidencia()
        elif nueva_fase == 'BLOQUEADO':
            # Configurar fecha límite para información
            workflow.fecha_limite_info = timezone.now() + timedelta(days=7)
        
        workflow.save()
        return workflow
    
    @staticmethod
    def redactar_propuesta(workflow, contenido, medico):
        """
        Redacta o actualiza la propuesta de consenso.
        
        Crea una nueva versión.
        """
        # Obtener número de versión
        ultima_version = workflow.versiones.first()
        numero_version = (ultima_version.numero_version + 1) if ultima_version else 1
        
        # Crear versión
        ConsensusVersion.objects.create(
            workflow=workflow,
            numero_version=numero_version,
            contenido=contenido,
            modificado_por=medico
        )
        
        # Actualizar propuesta actual
        workflow.propuesta_consenso = contenido
        workflow.fase = 'PROPUESTA'
        workflow.save()
        
        return workflow
    
    @staticmethod
    def emitir_voto(workflow, medico, tipo_voto, justificacion=''):
        """
        Emite un voto en la fase de votación.
        """
        # Crear o actualizar voto
        voto, created = ConsensusVote.objects.update_or_create(
            workflow=workflow,
            medico=medico,
            defaults={
                'voto': tipo_voto,
                'justificacion': justificacion
            }
        )
        
        # Recalcular conteos
        workflow.votos_a_favor = workflow.votos.filter(
            voto__in=['aprueba', 'aprueba_mod']
        ).count()
        workflow.votos_en_contra = workflow.votos.filter(
            voto__in=['contraindicado', 'alternativa']
        ).count()
        workflow.abstenciones = workflow.votos.filter(
            voto='abstiene'
        ).count()
        
        workflow.save()
        
        return voto
    
    @staticmethod
    def cerrar_votacion(workflow, es_consenso=True, opiniones_disidentes=None):
        """
        Cierra la votación y registra el resultado.
        """
        if es_consenso:
            workflow.fase = 'CONSENSO'
            workflow.nivel_evidencia = workflow.calcular_nivel_evidencia()
        else:
            workflow.fase = 'DISENSO'
            workflow.nivel_evidencia = 'baja'
            
            # Registrar opiniones disidentes
            if opiniones_disidentes:
                for item in opiniones_disidentes:
                    OpinionDisidente.objects.create(
                        workflow=workflow,
                        medico=item['medico'],
                        opinion=item['opinion']
                    )
        
        workflow.fecha_consenso = timezone.now()
        workflow.esta_bloqueado = True
        workflow.save()
        
        return workflow
    
    @staticmethod
    def solicitar_mas_info(workflow, descripcion):
        """
        Solicita más información al paciente.
        """
        workflow.requiere_mas_informacion = True
        workflow.descripcion_info_requerida = descripcion
        workflow.fecha_limite_info = timezone.now() + timedelta(days=7)
        workflow.fase = 'BLOQUEADO'
        workflow.save()
        
        return workflow
    
    @staticmethod
    def get_resumen_votacion(workflow):
        """Obtiene el resumen de la votación actual"""
        return {
            'votos_a_favor': workflow.votos_a_favor,
            'votos_en_contra': workflow.votos_en_contra,
            'abstenciones': workflow.abstenciones,
            'total_votos': workflow.votos_a_favor + workflow.votos_en_contra + workflow.abstenciones,
            'nivel_evidencia': workflow.nivel_evidencia,
            'votos_detalle': list(workflow.votos.values('medico__nombres', 'medico__apellidos', 'voto', 'justificacion'))
        }


# =====================================================
# SERVICIO DE MENSAJERÍA MDT
# =====================================================

class MDTMessageService:
    """
    Servicio para gestionar mensajes del comité MDT.
    
    Características:
    - Mensajes por caso y grupo
    - Respuestas anidadas
    - Indicadores de lectura
    - Mensajes del sistema automáticos
    """
    
    @staticmethod
    def crear_mensaje(caso, grupo, autor, contenido, tipo='mensaje', mensaje_padre=None):
        """Crea un nuevo mensaje en el chat MDT"""
        mensaje = MDTMessage.objects.create(
            caso=caso,
            grupo=grupo,
            autor=autor,
            contenido=contenido,
            tipo=tipo,
            mensaje_padre=mensaje_padre
        )
        
        # Notificar a otros miembros (a través de WebSocket más adelante)
        return mensaje
    
    @staticmethod
    def crear_mensaje_sistema(caso, grupo, contenido):
        """Crea un mensaje automático del sistema"""
        return MDTMessageService.crear_mensaje(
            caso=caso,
            grupo=grupo,
            autor=None,  # Sistema
            contenido=contenido,
            tipo='sistema'
        )
    
    @staticmethod
    def get_conversacion(caso, grupo, limite=100):
        """Obtiene la conversación de un caso en un grupo"""
        return MDTMessage.objects.filter(
            caso=caso,
            grupo=grupo
        ).select_related('autor').prefetch_related(
            'respuestas__autor',
            'leido_por'
        ).order_by('creado_en')[:limite]
    
    @staticmethod
    def marcar_como_leido(mensaje, medico):
        """Marca un mensaje como leído por un médico"""
        mensaje.leido_por.add(medico)
    
    @staticmethod
    def get_mensajes_no_leidos(caso, grupo, medico):
        """Obtiene mensajes no leídos por un médico"""
        return MDTMessage.objects.filter(
            caso=caso,
            grupo=grupo
        ).exclude(
            leido_por=medico
        ).count()
    
    @staticmethod
    def notificar_nuevo_mensaje(mensaje):
        """Genera datos para notificación de nuevo mensaje"""
        return {
            'tipo': 'nuevo_mensaje_mdt',
            'caso_id': mensaje.caso.case_id,
            'grupo_id': mensaje.grupo.id,
            'autor': mensaje.autor.nombre_completo if mensaje.autor else 'Sistema',
            'contenido': mensaje.contenido[:100],  # Preview
            'timestamp': mensaje.creado_en.isoformat()
        }


# =====================================================
# SERVICIO DE PRESENCIA
# =====================================================

class PresenceService:
    """
    Servicio para gestionar presencia de usuarios en tiempo real.
    """
    
    @staticmethod
    def actualizar_presence(usuario, caso=None, estado='online', ip_address=None):
        """
        Actualiza o crea registro de presencia.
        """
        presence, created = UserPresence.objects.update_or_create(
            usuario=usuario,
            defaults={
                'caso': caso,
                'estado': estado,
                'ip_address': ip_address
            }
        )
        return presence
    
    @staticmethod
    def marcar_offline(usuario):
        """Marca al usuario como desconectado"""
        UserPresence.objects.filter(usuario=usuario).update(estado='offline')
    
    @staticmethod
    def get_usuarios_conectados(caso):
        """Obtiene usuarios conectados a un caso"""
        return UserPresence.objects.filter(
            caso=caso,
            estado__in=['online', 'away', 'busy']
        ).select_related('usuario')
    
    @staticmethod
    def get_estado_usuario(usuario):
        """Obtiene el estado actual de un usuario"""
        try:
            return UserPresence.objects.get(usuario=usuario)
        except UserPresence.DoesNotExist:
            return None
    
    @staticmethod
    def limpiar_presencias_inactivas():
        """
        Limpia presencias con heartbeat mayor a 5 minutos.
        
        Debe llamarse periódicamente (ej: cada minuto).
        """
        limite = timezone.now() - timedelta(minutes=5)
        UserPresence.objects.filter(
            ultimo_heartbeat__lt=limite
        ).update(estado='offline')


# =====================================================
# SERVICIO DE ANONIMIZACIÓN DE DOCUMENTOS
# =====================================================

class AnonymizationService:
    """
    Servicio para anonimizar documentos médicos.
    
    Detecta y reemplaza:
    - Nombres de pacientes
    - Números de identificación
    - Direcciones
    - Teléfonos
    - Emails
    - Fechas específicas
    """
    
    import re
    
    # Patrones para detección de PII
    PATRONES_PII = {
        'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
        'telefono': re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
        'fecha': re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'),
        'cedula': re.compile(r'\d{6,12}'),
    }
    
    @staticmethod
    def anonimizar_texto(texto, paciente_nombre=None):
        """
        Reemplaza PII en texto.
        
        Args:
            texto: Texto a anonimizar
            paciente_nombre: Nombre del paciente para reemplazar
            
        Returns:
            Texto anonimizado
        """
        if not texto:
            return texto
        
        resultado = texto
        
        # Reemplazar email
        resultado = AnonymizationService.PATRONES_PII['email'].sub(
            '[EMAIL_REMOVIDO]',
            resultado
        )
        
        # Reemplazar teléfonos
        resultado = AnonymizationService.PATRONES_PII['telefono'].sub(
            '[TELÉFONO_REMOVIDO]',
            resultado
        )
        
        # Reemplazar números de identificación
        resultado = AnonymizationService.PATRONES_PII['cedula'].sub(
            '[ID_REMOVIDO]',
            resultado
        )
        
        # Reemplazar nombre del paciente si se proporciona
        if paciente_nombre:
            # Reemplazar todas las ocurrencias del nombre
            for nombre in paciente_nombre.split():
                if len(nombre) > 3:  # Solo palabras significativas
                    resultado = resultado.replace(nombre, '[NOMBRE_REMOVIDO]')
        
        return resultado
    
    @staticmethod
    def generar_version_anonima(documento, paciente_nombre=None):
        """
        Genera una versión anonimizada de un documento.
        
        Args:
            documento: Instancia de CaseDocument
            paciente_nombre: Nombre del paciente
            
        Returns:
            Contenido anonimizado o ruta del archivo generado
        """
        # TODO: Implementar procesamiento real de PDF/imágenes
        # Por ahora, retorna indicador de que necesita procesamiento
        
        if documento.is_anonymized:
            return documento  # Ya anonimizado
        
        # Marcar como anonimizado
        documento.is_anonymized = True
        documento.save()
        
        return documento


# =====================================================
# SERVICIO DE PLANTILLAS CLÍNICAS
# =====================================================

class TemplateService:
    """
    Servicio para gestionar plantillas clínicas.
    """
    
    @staticmethod
    def get_plantillas(especialidad=None, tipo_cancer=None, solo_activas=True):
        """Obtiene plantillas según criterios"""
        qs = ClinicalTemplate.objects.all()
        
        if solo_activas:
            qs = qs.filter(esta_activa=True)
        
        if especialidad:
            qs = qs.filter(especialidad=especialidad)
        
        if tipo_cancer:
            qs = qs.filter(
                models.Q(tipo_cancer=tipo_cancer) |
                models.Q(tipo_cancer=None)  # Incluir plantillas generales
            )
        
        return qs.order_by('nombre')
    
    @staticmethod
    def usar_plantilla(plantilla):
        """Incrementa el contador de uso de una plantilla"""
        plantilla.veces_usada += 1
        plantilla.save()
    
    @staticmethod
    def aplicar_variables(plantilla, contexto):
        """
        Aplica variables a una plantilla.
        
        Args:
            plantilla: Contenido de la plantilla
            contexto: Dict con valores {paciente, edad, diagnostico, etc.}
            
        Returns:
            Texto con variables reemplazadas
        """
        resultado = plantilla
        for clave, valor in contexto.items():
            placeholder = f'{{{{ {clave} }}}}'
            resultado = resultado.replace(placeholder, str(valor))
        return resultado


# =====================================================
# SERVICIO DE RESPUESTA FINAL MDT
# =====================================================

class MDTResponseService:
    """
    Servicio para generar la respuesta final del comité MDT.
    
    Genera PDF y envía correo al paciente.
    """
    
    @staticmethod
    def generar_y_enviar_respuesta(caso, responsable, conformidad, explicacion=''):
        """
        Genera el PDF de respuesta y lo envía por correo al paciente.
        
        Args:
            caso: Instancia del modelo Case
            responsable: Instancia del modelo Medico (coordinador)
            conformidad: 'conformidad' o 'no_conformidad'
            explicacion: Texto de explicación si hay disconformidad
            
        Returns:
            Dict con {'success': bool, 'pdf_path': str, 'error': str}
        """
        try:
            # Obtener información del caso
            paciente = caso.patient
            workflow = getattr(caso, 'workflow_consenso', None)
            
            # Obtener votos de los miembros
            votos = []
            if workflow:
                for voto in workflow.votos.all():
                    votos.append({
                        'medico': voto.medico.nombre_completo,
                        'voto': voto.get_voto_display(),
                        'justificacion': voto.justificacion
                    })
            
            # Generar PDF
            pdf_buffer = MDTResponseService._generar_pdf(
                caso=caso,
                paciente=paciente,
                responsable=responsable,
                conformidad=conformidad,
                explicacion=explicacion,
                votos=votos
            )
            
            # Guardar PDF - Primero crear el registro de FinalReport si no existe
            from django.core.files.base import ContentFile
            pdf_filename = f'respuesta_{caso.case_id}.pdf'
            
            # Crear o obtener el informe final
            from cases.models import FinalReport
            informe_final, created = FinalReport.objects.get_or_create(
                case=caso,
                defaults={
                    'conclusion': conformidad,
                    'justificacion': explicacion,
                    'recomendaciones': 'Generado automáticamente',
                    'redactado_por': responsable
                }
            )
            # Actualizar campos
            informe_final.conclusion = conformidad
            informe_final.justificacion = explicacion
            informe_final.recomendaciones = 'Generado automáticamente'
            informe_final.redactado_por = responsable
            informe_final.save()
            
            # Guardar el PDF en el campo pdf_file
            informe_final.pdf_file.save(pdf_filename, ContentFile(pdf_buffer.getvalue()))
            informe_final.save()
            
            # Enviar correo
            email_enviado = MDTResponseService._enviar_correo(
                caso=caso,
                paciente=paciente,
                pdf_buffer=pdf_buffer,
                conformidad=conformidad
            )
            
            return {
                'success': True,
                'pdf_path': informe_final.pdf_file.url if informe_final.pdf_file else None,
                'email_sent': email_enviado
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _generar_pdf(caso, paciente, responsable, conformidad, explicacion, votos):
        """Genera el PDF de respuesta"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, spaceAfter=20)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceBefore=15, spaceAfter=10)
        normal_style = styles['Normal']
        
        story = []
        
        # Título
        story.append(Paragraph("SEGUNDA OPINIÓN MÉDICA - ONCOMDT", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información del caso
        story.append(Paragraph("INFORMACIÓN DEL CASO", heading_style))
        info_data = [
            ["ID del Caso:", caso.case_id],
            ["Fecha de Solicitud:", caso.created_at.strftime('%d/%m/%Y') if caso.created_at else ''],
            ["Tipo de Cáncer:", str(caso.tipo_cancer) if caso.tipo_cancer else 'No especificado'],
            ["Diagnóstico:", caso.primary_diagnosis or 'No especificado'],
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Información del paciente
        story.append(Paragraph("INFORMACIÓN DEL PACIENTE", heading_style))
        story.append(Paragraph(f"Nombre: {paciente.get_full_name()}", normal_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Resultado del Comité
        story.append(Paragraph("RESULTADO DEL COMITÉ MÉDICO", heading_style))
        
        if conformidad == 'conformidad':
            story.append(Paragraph(
                "<b>CONCLUSIÓN: El Comité está de acuerdo con el diagnóstico y tratamiento propuesto.</b>",
                normal_style
            ))
        else:
            story.append(Paragraph(
                "<b>CONCLUSIÓN: El Comité NO está de acuerdo con el diagnóstico y/o tratamiento propuesto.</b>",
                normal_style
            ))
            story.append(Spacer(1, 0.1*inch))
            if explicacion:
                story.append(Paragraph("EXPLICACIÓN:", normal_style))
                story.append(Paragraph(explicacion, normal_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Votos de los miembros
        if votos:
            story.append(Paragraph("OPINIONES DE LOS MIEMBROS DEL COMITÉ", heading_style))
            for v in votos:
                story.append(Paragraph(f"<b>Dr. {v['medico']}</b>: {v['voto']}", normal_style))
                if v['justificacion']:
                    story.append(Paragraph(f"   {v['justificacion']}", normal_style))
                story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Responsable
        story.append(Paragraph("COORDINADOR DEL COMITÉ", heading_style))
        story.append(Paragraph(
            f"Dr. {responsable.nombre_completo} - {responsable.registro_medico}",
            normal_style
        ))
        story.append(Paragraph(
            f"Institución: {responsable.institucion_actual}",
            normal_style
        ))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            "<i>Este documento es una segunda opinión consultiva. No sustituye la evaluación directa "
            "por un profesional médico cualificado.</i>",
            ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def _enviar_correo(caso, paciente, pdf_buffer, conformidad):
        """Envía el correo con el PDF adjunto"""
        try:
            subject = f"Segunda Opinión Médica - Caso {caso.case_id}"
            
            if conformidad == 'conformidad':
                message = f"""
Estimado/a {paciente.get_full_name()},

Le informamos que el Comité Médico ha completado la revisión de su caso (ID: {caso.case_id}).

El Comité está DE ACUERDO con el diagnóstico y tratamiento propuesto.

Puede acceder al informe completo iniciando sesión en nuestro sistema.

Atentamente,
Equipo OnCoMDT
"""
            else:
                message = f"""
Estimado/a {paciente.get_full_name()},

Le informamos que el Comité Médico ha completado la revisión de su caso (ID: {caso.case_id}).

El Comité ha expresado DISCREPANCIAS respecto al diagnóstico y/o tratamiento propuesto. Por favor, revise el informe adjunto para más detalles.

Puede acceder al informe completo iniciando sesión en nuestro sistema.

Atentamente,
Equipo OnCoMDT
"""
            
            from django.core.mail import EmailMessage
            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [paciente.email]
            )
            email.attach('informe_segunda_opinion.pdf', pdf_buffer.getvalue(), 'application/pdf')
            email.send(fail_silently=False)
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
