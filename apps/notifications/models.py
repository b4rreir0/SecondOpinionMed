from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class EmailLog(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'
    STATUS_RETRYING = 'RETRYING'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_RETRYING, 'Retrying'),
    ]

    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    context_json = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    retries_attempted = models.PositiveIntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_sent(self):
        self.status = self.STATUS_SUCCESS
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])

    def mark_failed(self, error_message=None):
        self.status = self.STATUS_FAILED
        if error_message:
            self.error_message = str(error_message)
        self.sent_at = timezone.now()
        self.save()

    def mark_retrying(self, error_message=None):
        self.status = self.STATUS_RETRYING
        self.retries_attempted = (self.retries_attempted or 0) + 1
        if error_message:
            self.error_message = str(error_message)
        self.save()

    def __str__(self):
        return f"EmailLog {self.id} -> {self.recipient} [{self.status}]"


class EmailTemplate(models.Model):
    name = models.CharField(max_length=200, unique=True)
    subject = models.CharField(max_length=255)
    template_path = models.CharField(max_length=255, help_text='Django template path, e.g. emails/doctor_invite.html')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DoctorInvitation(models.Model):
    invited_email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return (not self.is_used) and (self.expires_at >= timezone.now())

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])

    def __str__(self):
        return f"Invite {self.invited_email} ({'used' if self.is_used else 'pending'})"


class PatientVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return (not self.is_verified) and (self.expires_at >= timezone.now())

    def mark_verified(self):
        self.is_verified = True
        self.save(update_fields=['is_verified'])

    def __str__(self):
        return f"PatientVerification {self.user.email} - {'verified' if self.is_verified else 'pending'}"


class Notification(models.Model):
    """
    Notificaciones in-app para usuarios del sistema.
    
    Almacena notificaciones que se muestran en la interfaz
    y pueden requerir acción del usuario.
    """
    
    TIPO_CHOICES = [
        ('asignacion_caso', 'Nuevo caso asignado'),
        ('nueva_opinion', 'Nueva opinión en caso'),
        ('recordatorio_voto', 'Recordatorio de votación'),
        ('votacion_cerrada', 'Votación cerrada'),
        ('informe_disponible', 'Informe final disponible'),
        ('caso_actualizado', 'Caso actualizado'),
        ('documento_subido', 'Nuevo documento subido'),
    ]
    
    receptor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        help_text="Tipo de notificación"
    )
    titulo = models.CharField(
        max_length=200,
        help_text="Título de la notificación"
    )
    mensaje = models.TextField(
        help_text="Cuerpo del mensaje"
    )
    enlace = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL de acción (opcional)"
    )
    leido = models.BooleanField(
        default=False,
        help_text="Indica si la notificación ha sido leída"
    )
    
    # Referencia opcional al caso relacionado
    caso_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="ID del caso relacionado"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se leyó la notificación"
    )
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['receptor', 'leido']),
            models.Index(fields=['receptor', '-fecha_creacion']),
        ]
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        self.leido = True
        self.fecha_lectura = timezone.now()
        self.save(update_fields=['leido', 'fecha_lectura'])
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.receptor.email} - {'Leída' if self.leido else 'No leída'}"
