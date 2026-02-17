"""
Modelos para funcionalidades P0 del sistema MDT.

Este módulo contiene los modelos para:
- Mensajería MDT (chat por comité)
- Configuración del algoritmo de asignación
- Workflow de consenso formal
- Presencia de usuarios en tiempo real
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import TimeStampedModel


class MDTMessage(TimeStampedModel):
    """
    Mensaje en el chat del comité MDT.
    
    Cada mensaje pertenece a un caso específico y un grupo médico específico.
    Solo los miembros del grupo pueden ver y enviar mensajes.
    """
    
    TIPO_CHOICES = [
        ('mensaje', 'Mensaje'),
        ('sistema', 'Mensaje del Sistema'),
        ('adjunto', 'Adjunto'),
    ]
    
    caso = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='mdt_messages'
    )
    grupo = models.ForeignKey(
        'medicos.MedicalGroup',
        on_delete=models.CASCADE,
        related_name='messages'
    )
    autor = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE,
        related_name='mdt_messages'
    )
    
    # Contenido
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='mensaje'
    )
    contenido = models.TextField()
    
    # Para respuestas/nested threads
    mensaje_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='respuestas'
    )
    
    # Estado
    es_privado = models.BooleanField(
        default=False,
        help_text="Si es True, solo el autor puede ver el mensaje"
    )
    esta_editado = models.BooleanField(default=False)
    
    # Lectura
    leido_por = models.ManyToManyField(
        'medicos.Medico',
        related_name='mensajes_leidos',
        blank=True
    )
    
    class Meta:
        ordering = ['creado_en']
        indexes = [
            models.Index(fields=['caso', '-creado_en']),
            models.Index(fields=['grupo', '-creado_en']),
        ]
    
    def __str__(self):
        return f"Mensaje de {self.autor.nombre_completo} en caso {self.caso.case_id}"


class MDTMessageAttachment(TimeStampedModel):
    """Adjuntos en mensajes MDT"""
    
    mensaje = models.ForeignKey(
        MDTMessage,
        on_delete=models.CASCADE,
        related_name='adjuntos'
    )
    archivo = models.FileField(upload_to='mdt/attachments/%Y/%m/')
    nombre_original = models.CharField(max_length=255)
    tipo_mime = models.CharField(max_length=100)
    tamano = models.PositiveIntegerField()
    
    def __str__(self):
        return f"Adjunto: {self.nombre_original}"


class UserPresence(TimeStampedModel):
    """
    Control de presencia de usuarios en tiempo real.
    
    Registra cuando un médico está conectado, ausente, o en una videollamada.
    """
    
    ESTADO_CHOICES = [
        ('online', 'Conectado'),
        ('away', 'Ausente'),
        ('busy', 'En Llamada/Videollamada'),
        ('offline', 'Desconectado'),
    ]
    
    usuario = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE,
        related_name='presencias'
    )
    caso = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='participantes_conectados'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='offline'
    )
    ultimo_heartbeat = models.DateTimeField(auto_now=True)
    
    # IP y user agent para debugging
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-ultimo_heartbeat']
        indexes = [
            models.Index(fields=['usuario', '-ultimo_heartbeat']),
            models.Index(fields=['caso', 'estado']),
        ]
    
    def __str__(self):
        return f"{self.usuario.nombre_completo} - {self.get_estado_display()}"
    
    @property
    def esta_activo(self):
        """Verifica si el heartbeat es reciente (menos de 5 minutos)"""
        diff = timezone.now() - self.ultimo_heartbeat
        return diff.seconds < 300  # 5 minutos


class AlgoritmoConfig(TimeStampedModel):
    """
    Configuración global del algoritmo de asignación de casos.
    
    Permite ajustar el comportamiento del sistema round-robin.
    """
    
    nombre = models.CharField(
        max_length=100,
        unique=True,
        default='configuracion_default'
    )
    
    # Ponderación (0-100)
    ponderacion_carga = models.PositiveIntegerField(
        default=50,
        help_text="Peso de la carga actual vs antigüedad (0 = solo antigüedad, 100 = solo carga)"
    )
    
    # Modo de operación
    modo_estricto = models.BooleanField(
        default=False,
        help_text="Si True, ignora ponderaciones y usa round-robin puro"
    )
    
    # Límites
    limite_mensual_por_medico = models.PositiveIntegerField(
        default=15,
        help_text="Límite máximo de casos por médico por mes"
    )
    
    permitir_overrides = models.BooleanField(
        default=True,
        help_text="Permite que el administrador asigne manualmente casos"
    )
    
    # Respetar disponibilidad
    respetar_disponibilidad = models.BooleanField(
        default=True,
        help_text="Si True, no asigna a médicos marcados como no disponibles"
    )
    
    # Auditoría
    activo = models.BooleanField(default=True)
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='configs_algoritmo'
    )
    
    class Meta:
        verbose_name = 'Configuración del Algoritmo'
        verbose_name_plural = 'Configuraciones del Algoritmo'
    
    def __str__(self):
        return f"Config: {self.nombre} (ponderación: {self.ponderacion_carga}%)"


class AsignacionAuditLog(TimeStampedModel):
    """
    Registro de auditoría de cada asignación de caso.
    
    Mantiene un historial de por qué se seleccionó un médico específico.
    """
    
    caso = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='audit_asignaciones'
    )
    
    medico_seleccionado = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.SET_NULL,
        null=True,
        related_name='asignaciones_recibidas'
    )
    
    # Detalles de la decisión
    decision = models.CharField(
        max_length=50,
        help_text="Resultado: asignado, saltado, no_disponible"
    )
    motivo = models.TextField(
        help_text="Razón de la decisión (ej: 'Carga mínima', 'No disponible')"
    )
    
    # Scores calculados
    score_carga = models.FloatField(null=True, blank=True)
    score_antiguedad = models.FloatField(null=True, blank=True)
    score_final = models.FloatField(null=True, blank=True)
    
    # Configuración usada
    config = models.ForeignKey(
        AlgoritmoConfig,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs_asignacion'
    )
    
    # Override manual
    es_override = models.BooleanField(default=False)
    override_justificacion = models.TextField(blank=True)
    override_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='overrides_asignacion'
    )
    
    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Log de Asignación'
        verbose_name_plural = 'Logs de Asignación'
    
    def __str__(self):
        return f"Asignación caso {self.caso.case_id} -> Dr. {self.medico_seleccionado}"


class ConsensusWorkflow(TimeStampedModel):
    """
    Workflow formal de consenso MDT para un caso.
    
    Gestiona las fases: Discusión Abierta -> Propuesta -> Votación -> Consenso/Disenso
    """
    
    FASE_CHOICES = [
        ('DISCUSION', 'Discusión Abierta'),
        ('PROPUESTA', 'Propuesta Redactada'),
        ('VOTACION', 'Votación Abierta'),
        ('CONSENSO', 'Consenso Alcanzado'),
        ('DISENSO', 'Disenso Registrado'),
        ('BLOQUEADO', 'Bloqueado - Más Info'),
    ]
    
    NIVEL_EVIDENCIA_CHOICES = [
        ('alta', 'Alta - Unánime'),
        ('moderada', 'Moderada - Mayoría Simple'),
        ('baja', 'Baja - Disenso Significativo'),
    ]
    
    caso = models.OneToOneField(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='workflow_consenso'
    )
    
    fase = models.CharField(
        max_length=20,
        choices=FASE_CHOICES,
        default='DISCUSION'
    )
    
    # Propuesta de consenso
    propuesta_consenso = models.TextField(
        blank=True,
        help_text="Borrador de consenso redactado por el coordinador"
    )
    
    # Votación
    votos_a_favor = models.PositiveIntegerField(default=0)
    votos_en_contra = models.PositiveIntegerField(default=0)
    abstenciones = models.PositiveIntegerField(default=0)
    
    # Resultado
    nivel_evidencia = models.CharField(
        max_length=20,
        choices=NIVEL_EVIDENCIA_CHOICES,
        blank=True
    )
    
    # Información adicional requerida
    requiere_mas_informacion = models.BooleanField(default=False)
    descripcion_info_requerida = models.TextField(blank=True)
    fecha_limite_info = models.DateField(null=True, blank=True)
    
    # Fechas
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_consenso = models.DateTimeField(null=True, blank=True)
    
    # Cerrado
    esta_bloqueado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Workflow de Consenso'
        verbose_name_plural = 'Workflows de Consenso'
    
    def __str__(self):
        return f"Consenso caso {self.caso.case_id} - Fase: {self.get_fase_display()}"
    
    def calcular_nivel_evidencia(self):
        """Calcula el nivel de evidencia basado en los votos"""
        total = self.votos_a_favor + self.votos_en_contra + self.abstenciones
        if total == 0:
            return None
        
        if self.votos_en_contra == 0 and self.abstenciones == 0:
            return 'alta'
        elif self.votos_a_favor > self.votos_en_contra:
            return 'moderada'
        return 'baja'
    
    def puede_cerrar(self):
        """Verifica si el workflow puede cerrarse"""
        return self.fase in ['VOTACION', 'CONSENSO', 'DISENSO', 'BLOQUEADO']


class ConsensusVersion(TimeStampedModel):
    """
    Control de versiones del borrador de consenso.
    
    Cada cambio en la propuesta genera una nueva versión.
    """
    
    workflow = models.ForeignKey(
        ConsensusWorkflow,
        on_delete=models.CASCADE,
        related_name='versiones'
    )
    
    numero_version = models.PositiveIntegerField()
    contenido = models.TextField()
    modificado_por = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.SET_NULL,
        null=True,
        related_name='versiones_consenso'
    )
    
    notas_cambio = models.TextField(
        blank=True,
        help_text="Descripción de los cambios realizados"
    )
    
    class Meta:
        ordering = ['-numero_version']
        verbose_name = 'Versión de Consenso'
        verbose_name_plural = 'Versiones de Consenso'
    
    def __str__(self):
        return f"Versión {self.numero_version} - Workflow {self.workflow.id}"


class ConsensusVote(TimeStampedModel):
    """
    Voto individual de un médico en el proceso de consenso.
    """
    
    VOTO_CHOICES = [
        ('aprueba', 'Aprueba'),
        ('aprueba_mod', 'Aprueba con Modificaciones'),
        ('alternativa', 'Propone Alternativa'),
        ('contraindicado', 'Considera Contraindicado'),
        ('abstiene', 'Se Abstiene'),
    ]
    
    workflow = models.ForeignKey(
        ConsensusWorkflow,
        on_delete=models.CASCADE,
        related_name='votos'
    )
    medico = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE,
        related_name='votos_consenso'
    )
    
    voto = models.CharField(max_length=20, choices=VOTO_CHOICES)
    justificacion = models.TextField(
        blank=True,
        help_text="Razón del voto"
    )
    
    class Meta:
        verbose_name = 'Voto de Consenso'
        verbose_name_plural = 'Votos de Consenso'
        constraints = [
            models.UniqueConstraint(
                fields=['workflow', 'medico'],
                name='unique_vote_per_workflow'
            )
        ]
    
    def __str__(self):
        return f"{self.medico.nombre_completo}: {self.get_voto_display()}"


class OpinionDisidente(TimeStampedModel):
    """
    Registro de opiniones disidentes cuando no hay consenso unanime.
    """
    
    workflow = models.ForeignKey(
        ConsensusWorkflow,
        on_delete=models.CASCADE,
        related_name='opiniones_disidentes'
    )
    medico = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE,
        related_name='opiniones_disidentes'
    )
    
    opinion = models.TextField()
    
    class Meta:
        verbose_name = 'Opinión Disidente'
        verbose_name_plural = 'Opiniones Disidentes'
    
    def __str__(self):
        return f"Disidencia Dr. {self.medico.nombre_completo}"


class ClinicalTemplate(TimeStampedModel):
    """
    Plantillas clínicas para dictados médicos.
    
    Organizadas por especialidad y tipo de cáncer.
    """
    
    nombre = models.CharField(max_length=200)
    especialidad = models.ForeignKey(
        'medicos.Especialidad',
        on_delete=models.SET_NULL,
        null=True,
        related_name='plantillas'
    )
    tipo_cancer = models.ForeignKey(
        'medicos.TipoCancer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plantillas'
    )
    
    # Contenido de la plantilla
    contenido = models.TextField(
        help_text="Plantilla con variables como {{paciente}}, {{edad}}, etc."
    )
    
    # Metadatos
    es_global = models.BooleanField(
        default=True,
        help_text="Si True, es institucional; si False, es personal del médico"
    )
    creador = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plantillas_creadas'
    )
    esta_activa = models.BooleanField(default=True)
    
    # Usage tracking
    veces_usada = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Plantilla Clínica'
        verbose_name_plural = 'Plantillas Clínicas'
    
    def __str__(self):
        return f"{self.nombre} ({self.especialidad})"


class AnatomicalRegion(models.Model):
    """
    Regiones anatómicas para el mapeo en el wizard de intake.
    
    Mapea regiones del cuerpo a especialidades sugeridas.
    """
    
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True)
    
    # SVG path o identificador para el mapa corporal
    svg_path = models.TextField(blank=True)
    svg_id = models.CharField(max_length=50, blank=True)
    
    # Especialidades sugeridas para esta región
    especialidades_sugeridas = models.ManyToManyField(
        'medicos.Especialidad',
        related_name='regiones_anatomicas'
    )
    
    # Síntomas asociados (keywords)
    sintomas_asociados = models.JSONField(
        default=list,
        help_text="Lista de síntomas típicos de esta región"
    )
    
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Región Anatómica'
        verbose_name_plural = 'Regiones Anatómicas'
    
    def __str__(self):
        return self.nombre


class UserPreferences(models.Model):
    """
    Preferencias de interfaz por usuario.
    
    Almacena preferencias como tema (oscuro/claro), idioma, etc.
    """
    
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferencias'
    )
    
    # Tema
    TEMA_CHOICES = [
        ('light', 'Claro'),
        ('dark', 'Oscuro'),
        ('system', 'Seguir Sistema'),
    ]
    tema = models.CharField(
        max_length=10,
        choices=TEMA_CHOICES,
        default='system'
    )
    
    # Idioma
    idioma = models.CharField(
        max_length=10,
        default='es'
    )
    
    # Notificaciones
    notificaciones_email = models.BooleanField(default=True)
    notificaciones_push = models.BooleanField(default=True)
    
    # Dashboard
    elementos_por_pagina = models.PositiveIntegerField(default=10)
    
    class Meta:
        verbose_name = 'Preferencia de Usuario'
        verbose_name_plural = 'Preferencias de Usuarios'
    
    def __str__(self):
        return f"Preferencias de {self.usuario.email}"
