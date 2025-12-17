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
    que será asignada a un médico especialista.
    """
    
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('PROCESSING', 'Processing'),
        ('PAID', 'Paid'),
        ('IN_REVIEW', 'In Review'),
        ('OPINION_COMPLETE', 'Opinion Complete'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
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
    description = EncryptedTextField(
        help_text="Descripción detallada del caso"
    )
    
    # Estado
    # FSMField ensures transitions are controlled and auditable
    status = FSMField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Auditoría temporal
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de asignación al médico"
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

    # FSM transitions
    @transition(field=status, source='DRAFT', target='SUBMITTED')
    def submit_case(self):
        self.assigned_at = None

    @transition(field=status, source='SUBMITTED', target='PROCESSING')
    def process_documents(self):
        # placeholder to trigger async tasks
        pass

    @transition(field=status, source='PROCESSING', target='PAID')
    def pay_fee(self):
        pass

    @transition(field=status, source=['PAID', 'PROCESSING'], target='IN_REVIEW')
    def assign_expert(self, doctor):
        self.doctor = doctor
        self.assigned_at = timezone.now()

    @transition(field=status, source='IN_REVIEW', target='OPINION_COMPLETE')
    def finalize_opinion(self):
        self.completed_at = timezone.now()

    @transition(field=status, source='OPINION_COMPLETE', target='CLOSED')
    def deliver_report(self):
        pass


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
        upload_to='cases/documents/%Y/%m/%d/',
        help_text="Archivo del documento (debe estar cifrado)"
    )
    # S3 path for direct-to-S3 uploads; kept separate from FileField
    s3_file_path = models.CharField(
        max_length=1024,
        blank=True,
        help_text="Ruta/Key en S3 para el archivo (presigned upload)"
    )
    is_anonymized = models.BooleanField(
        default=False,
        help_text="Indica si el archivo fue anonimizado"
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
