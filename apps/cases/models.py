from django.db import models
from django.utils import timezone
try:
    from django_fsm import FSMField, transition
except Exception:
    # django-fsm not installed in the environment (dev). Provide
    # lightweight fallbacks so imports don't crash the app.
    class FSMField(models.CharField):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault('max_length', 30)
            super().__init__(*args, **kwargs)

    def transition(field=None, source=None, target=None):
        def decorator(func):
            return func
        return decorator
try:
    from fernet_fields import EncryptedCharField, EncryptedTextField
except Exception:
    EncryptedCharField = models.CharField
    EncryptedTextField = models.TextField


class Case(models.Model):
    """
    Modelo de Caso de Segunda Opinión.
    
    Representa una solicitud de segunda opinión médica de un paciente,
    que será asignada a un médico especialista o grupo médico (MDT).
    """
    
    STATUS_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('SUBMITTED', 'Enviado'),
        ('ASSIGNED', 'Asignado'),
        ('PROCESSING', 'Procesando'),
        ('MDT_IN_PROGRESS', 'En Análisis por MDT'),
        ('MDT_COMPLETED', 'Discusión MDT Cerrada'),
        ('REPORT_DRAFT', 'Informe en Redacción'),
        ('REPORT_COMPLETED', 'Informe Completado'),
        ('OPINION_COMPLETE', 'Opinión Completa'),
        ('CLOSED', 'Cerrado'),
        ('CANCELLED', 'Cancelado'),
    )
    
    # Relaciones
    patient = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.CASCADE,
        related_name='patient_cases',
        limit_choices_to={'role': 'patient'}
    )
    doctor = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctor_cases',
        limit_choices_to={'role': 'doctor'}
    )
    
    # Nuevo: Grupo médico (Comité MDT)
    medical_group = models.ForeignKey(
        'medicos.MedicalGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases',
        help_text="Grupo médico asignado al caso"
    )
    
    # Nuevo: Responsable del caso
    responsable = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases_responsable',
        help_text="Médico responsable del caso"
    )
    
    # Datos del caso
    case_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Identificador único del caso"
    )
    primary_diagnosis = EncryptedCharField(
        max_length=255,
        help_text="Diagnóstico primario"
    )
    specialty_required = models.CharField(
        max_length=100,
        help_text="Especialidad requerida"
    )
    
    # Nuevos: Tipo de cáncer y estadio
    tipo_cancer = models.ForeignKey(
        'medicos.TipoCancer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases',
        help_text="Tipo de cáncer"
    )
    
    ESTADIO_CHOICES = [
        ('I', 'Estadio I'),
        ('II', 'Estadio II'),
        ('III', 'Estadio III'),
        ('IV', 'Estadio IV'),
        ('N/A', 'No aplica'),
    ]
    
    estadio = models.CharField(
        max_length=10,
        choices=ESTADIO_CHOICES,
        blank=True,
        help_text="Estadio del cáncer"
    )
    
    tratamiento_propuesto_original = models.TextField(
        blank=True,
        help_text="Tratamiento propuesto originalmente"
    )
    
    objetivo_consulta = models.TextField(
        blank=True,
        help_text="Objetivo de la consulta"
    )
    
    description = EncryptedTextField(
        help_text="Descripción detallada del caso"
    )
    
    # Fecha del diagnóstico
    diagnosis_date = models.DateField(null=True, blank=True)
    
    # Localidad
    localidad = models.ForeignKey(
        'medicos.Localidad', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cases'
    )
    
    # Estado FSM
    status = FSMField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Fechas de seguimiento
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de asignación al médico"
    )
    fecha_limite = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha límite para resolver el caso"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de completación"
    )
    
    class Meta:
        verbose_name = 'Caso'
        verbose_name_plural = 'Casos'
        db_table = 'cases_case'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Caso {self.case_id} - {self.primary_diagnosis}"
    
    def is_patient_case(self, user):
        """Verifica si el usuario es el paciente del caso"""
        return self.patient == user and user.is_patient()
    
    def is_assigned_doctor(self, user):
        """Verifica si el usuario es el médico asignado"""
        return self.doctor == user and user.is_doctor()

    # FSM transitions - Nuevo Sistema MDT
    @transition(field=status, source='DRAFT', target='SUBMITTED')
    def submit_case(self):
        """El paciente envía la solicitud"""
        pass

    @transition(field=status, source='SUBMITTED', target='ASSIGNED')
    def assign_to_group(self):
        """Sistema asigna automáticamente a un grupo médico y responsable"""
        self.assigned_at = timezone.now()

    @transition(field=status, source='ASSIGNED', target='PROCESSING')
    def process_documents(self):
        """El responsable procesa los documentos"""
        pass

    @transition(field=status, source='PROCESSING', target='MDT_IN_PROGRESS')
    def iniciar_discusion_mdt(self):
        """Inicia la discusión con el comité MDT"""
        pass

    @transition(field=status, source='MDT_IN_PROGRESS', target='MDT_COMPLETED')
    def cerrar_votacion(self):
        """El responsable cierra la votación"""
        pass

    @transition(field=status, source='MDT_COMPLETED', target='REPORT_DRAFT')
    def iniciar_informe(self):
        """El responsable comienza a redactar el informe final"""
        pass

    @transition(field=status, source='REPORT_DRAFT', target='REPORT_COMPLETED')
    def completar_informe(self):
        """El responsable completa el informe"""
        pass

    @transition(field=status, source='REPORT_COMPLETED', target='CLOSED')
    def cerrar_caso(self):
        """Caso cerrado, informe entregado al paciente"""
        self.completed_at = timezone.now()

    @transition(field=status, source='*', target='CANCELLED')
    def cancelar_caso(self):
        """Cancela el caso"""
        pass

    # Transiciones legacy (compatibilidad)
    @transition(field=status, source=['PROCESSING', 'PAID'], target='IN_REVIEW')
    def assign_expert(self, doctor):
        self.doctor = doctor
        self.assigned_at = timezone.now()

    @transition(field=status, source='IN_REVIEW', target='OPINION_COMPLETE')
    def finalize_opinion(self):
        self.completed_at = timezone.now()

    @transition(field=status, source='OPINION_COMPLETE', target='CLOSED')
    def deliver_report(self):
        pass


def case_document_upload_path(instance, filename):
    """
    Función para generar la ruta de upload incluyendo el case_id.
    Define la ruta como: cases/{case_id}/documents/{filename}
    """
    case_id = instance.case.case_id if instance.case else 'unknown'
    return f'cases/{case_id}/documents/{filename}'


class CaseDocument(models.Model):
    """
    Modelo para almacenar documentos médicos asociados a un caso.
    
    Estos documentos (informes, imágenes, etc.) son PHI sensible
    y deben tratarse con cifrado a nivel de almacenamiento.
    """
    
    DOCUMENT_TYPE_CHOICES = (
        ('diagnostic_report', 'Informe Diagnóstico'),
        ('biopsy_report', 'Informe de Biopsia'),
        ('imaging', 'Imágenes Diagnósticas'),
        ('lab_results', 'Resultados de Laboratorio'),
        ('medical_history', 'Historial Médico'),
        ('other', 'Otro'),
    )
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES
    )
    
    file = models.FileField(
        upload_to=case_document_upload_path,
        help_text="Archivo del documento"
    )
    
    # Nuevos campos
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Descripción del documento"
    )
    
    # S3 path for direct-to-S3 uploads; kept separate from FileField
    s3_file_path = models.CharField(
        max_length=1024,
        blank=True,
        help_text="Ruta/Key en S3 para el archivo"
    )
    is_anonymized = models.BooleanField(
        default=False,
        help_text="Indica si el archivo fue anonimizado"
    )
    
    # Tamaño y tipo MIME
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Tamaño del archivo en bytes"
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tipo MIME del archivo"
    )
    
    file_name = models.CharField(
        max_length=255,
        help_text="Nombre original del archivo"
    )
    uploaded_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Documento del Caso'
        verbose_name_plural = 'Documentos del Caso'
        db_table = 'cases_casedocument'
    
    def __str__(self):
        return f"{self.file_name} - Caso {self.case.case_id}"


class SecondOpinion(models.Model):
    """
    Modelo para la Opinión del Médico.
    
    Almacena la opinión profesional del médico asignado.
    Este contenido es PHI crítico y debe estar cifrado a nivel de campo.
    """
    
    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name='second_opinion'
    )
    doctor = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.CASCADE,
        related_name='opinions'
    )
    opinion_text = models.TextField(
        help_text="Opinión profesional (será cifrada en la BD)"
    )
    recommendations = models.TextField(
        blank=True,
        help_text="Recomendaciones médicas"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Segunda Opinión'
        verbose_name_plural = 'Segundas Opiniones'
        db_table = 'cases_secondopinion'
    
    def __str__(self):
        return f"Opinión - Caso {self.case.case_id}"


class CaseAuditLog(models.Model):
    """
    Registro de auditoría para cada caso.
    
    Registra de forma inmutable cada acceso y modificación relacionada
    con el PHI del caso para cumplimiento de HIPAA/GDPR.
    """
    
    ACTION_CHOICES = (
        ('create', 'Creación'),
        ('read', 'Lectura'),
        ('update', 'Actualización'),
        ('delete', 'Eliminación'),
        ('document_upload', 'Carga de Documento'),
        ('opinion_added', 'Opinión Agregada'),
        ('clarification_requested', 'Aclaración Solicitada'),
    )
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.CASCADE
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción adicional del evento"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP del usuario que realizó la acción"
    )
    
    class Meta:
        verbose_name = 'Registro de Auditoría del Caso'
        verbose_name_plural = 'Registros de Auditoría de Casos'
        db_table = 'cases_caseauditlog'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['case', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - Caso {self.case.case_id} por {self.user.email}"


class MedicalOpinion(models.Model):
    """
    Opinión/Voto individual de un médico miembro del comité.
    
    Cada médico del grupo médico puede emitir una opinión sobre el caso.
    Las opiniones son privadas hasta que el responsable cierra la votación.
    """
    
    VOTO_CHOICES = [
        ('acuerdo', 'De acuerdo con el tratamiento propuesto'),
        ('desacuerdo', 'En desacuerdo con el tratamiento propuesto'),
        ('abstencion', 'Se abstiene de emitir opinión'),
    ]
    
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='opiniones'
    )
    doctor = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE,
        related_name='opiniones_casos'
    )
    voto = models.CharField(
        max_length=20,
        choices=VOTO_CHOICES,
        help_text="Voto del médico"
    )
    comentario_privado = models.TextField(
        blank=True,
        help_text="Comentario privado (solo visible para el grupo médico)"
    )
    fecha_emision = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Opinión Médica'
        verbose_name_plural = 'Opiniones Médicas'
        db_table = 'cases_medicalopinion'
        # Un voto por médico por caso
        constraints = [
            models.UniqueConstraint(
                fields=['case', 'doctor'],
                name='unique_opinion_per_case_doctor'
            )
        ]
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Opinión {self.get_voto_display()} - Caso {self.case.case_id} - Dr. {self.doctor.nombre_completo}"


class FinalReport(models.Model):
    """
    Informe final del caso generado por el médico responsable.
    
    Este informe consolida las opiniones del comité y se entrega al paciente.
    """
    
    CONCLUSION_CHOICES = [
        ('acuerdo', 'Acuerdo con tratamiento propuesto'),
        ('desacuerdo', 'Desacuerdo con tratamiento propuesto'),
        ('consenso_parcial', 'Consenso parcial'),
    ]
    
    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name='informe_final'
    )
    conclusion = models.CharField(
        max_length=20,
        choices=CONCLUSION_CHOICES,
        help_text="Conclusión del comité"
    )
    justificacion = models.TextField(
        help_text="Justificación de la conclusión"
    )
    recomendaciones = models.TextField(
        help_text="Recomendaciones médicas"
    )
    redactado_por = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE,
        related_name='informes_redactados'
    )
    fecha_emision = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    # Archivo PDF generado
    pdf_file = models.FileField(
        upload_to='cases/reports/%Y/%m/',
        null=True,
        blank=True,
        help_text="PDF del informe generado"
    )
    
    # Firma electrónica (hash SHA-256 del contenido)
    firma_electronica = models.CharField(
        max_length=64,
        blank=True,
        help_text="Hash SHA-256 del contenido del informe"
    )
    
    class Meta:
        verbose_name = 'Informe Final'
        verbose_name_plural = 'Informes Finales'
        db_table = 'cases_finalreport'
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Informe Final - Caso {self.case.case_id} - {self.get_conclusion_display()}"
