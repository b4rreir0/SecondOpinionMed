from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone
import secrets
try:
    from fernet_fields import EncryptedTextField, EncryptedCharField
except Exception:
    # Fallback to plain fields when the package is not installed (development)
    EncryptedTextField = models.TextField
    EncryptedCharField = models.CharField


class CustomUser(AbstractUser):
    """
    Modelo de usuario extendido que reemplaza el modelo predeterminado de Django.
    
    Esto proporciona flexibilidad para futuras mejoras y gestión explícita de roles.
    Almacena las credenciales de autenticación universales (email, hash de contraseña).
    """
    
    ROLE_CHOICES = (
        ('patient', 'Paciente'),
        ('doctor', 'Médico'),
    )
    
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text="Email único para autenticación"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='patient',
        help_text="Rol del usuario en el sistema"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Indica si el usuario puede acceder al sistema. Se activa después de verificar email"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Indica si el email ha sido verificado"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'auth_customuser'
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def is_patient(self):
        """Verifica si el usuario es un paciente"""
        return self.role == 'patient'
    
    def is_doctor(self):
        """Verifica si el usuario es un médico"""
        return self.role == 'doctor'


class PatientProfile(models.Model):
    """
    Perfil del Paciente.
    
    Enlazado al CustomUser, almacena los datos sensibles de identificación personal
    y médica del paciente (PHI). Estos campos críticos deben usar cifrado a nivel
    de campo en futuras implementaciones.
    """
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        limit_choices_to={'role': 'patient'}
    )
    
    # Datos de identificación personal (PHI)
    full_name = EncryptedCharField(
        max_length=255,
        help_text="Nombre completo del paciente"
    )
    identity_document = EncryptedCharField(
        max_length=50,
        unique=True,
        help_text="Cédula de identidad o pasaporte"
    )
    phone_number = EncryptedCharField(
        max_length=20,
        help_text="Número de teléfono de contacto"
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de nacimiento"
    )
    
    # Datos médicos
    primary_diagnosis = EncryptedTextField(
        blank=True,
        help_text="Diagnóstico primario"
    )
    medical_history = EncryptedTextField(
        blank=True,
        help_text="Historial médico relevante"
    )
    current_treatment = EncryptedTextField(
        blank=True,
        help_text="Tratamiento actual"
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Paciente'
        verbose_name_plural = 'Perfiles de Pacientes'
        db_table = 'auth_patientprofile'
    
    def __str__(self):
        return f"Paciente: {self.full_name}"


class DoctorProfile(models.Model):
    """
    Perfil del Médico.
    
    Enlazado al CustomUser, almacena credenciales profesionales,
    especializaciones y disponibilidad.
    """
    
    SPECIALTY_CHOICES = (
        ('oncology', 'Oncología'),
        ('cardiology', 'Cardiología'),
        ('neurology', 'Neurología'),
        ('orthopedics', 'Ortopedia'),
        ('general', 'Medicina General'),
        ('other', 'Otra'),
    )
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        limit_choices_to={'role': 'doctor'}
    )
    
    # Datos profesionales
    full_name = models.CharField(
        max_length=255,
        help_text="Nombre completo del médico"
    )
    medical_license = models.CharField(
        max_length=100,
        unique=True,
        help_text="Número de licencia médica"
    )
    specialty = models.CharField(
        max_length=50,
        choices=SPECIALTY_CHOICES,
        help_text="Especialidad médica"
    )
    phone_number = models.CharField(
        max_length=20,
        help_text="Número de teléfono profesional"
    )
    institution = models.CharField(
        max_length=255,
        blank=True,
        help_text="Institución o clínica"
    )
    
    # Disponibilidad
    is_available = models.BooleanField(
        default=True,
        help_text="Indica si el médico puede recibir nuevos casos"
    )
    max_concurrent_cases = models.PositiveIntegerField(
        default=10,
        help_text="Número máximo de casos simultáneos"
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Médico'
        verbose_name_plural = 'Perfiles de Médicos'
        db_table = 'auth_doctorprofile'
    
    def __str__(self):
        return f"Dr/Dra. {self.full_name} ({self.get_specialty_display()})"
    
    def current_case_count(self):
        """Retorna el número de casos activos del médico"""
        return self.doctor_cases.filter(status__in=['paid', 'in_review']).count()
    
    def can_accept_case(self):
        """Verifica si el médico puede aceptar un nuevo caso"""
        return self.is_available and self.current_case_count() < self.max_concurrent_cases

class EmailVerificationToken(models.Model):
    """
    Modelo para gestionar tokens de verificación de email.
    
    Almacena tokens únicos que se envían por correo para verificar
    la dirección de email del usuario.
    """
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='verification_token',
        help_text="Usuario asociado al token"
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        help_text="Token único de verificación"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="Fecha y hora de expiración del token"
    )
    is_used = models.BooleanField(
        default=False,
        help_text="Indica si el token ya ha sido utilizado"
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora cuando el token fue utilizado"
    )
    
    class Meta:
        verbose_name = 'Token de Verificación'
        verbose_name_plural = 'Tokens de Verificación'
        db_table = 'auth_emailverificationtoken'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Token para {self.user.email}"
    
    def is_valid(self):
        """Verifica si el token es válido y no ha expirado"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @staticmethod
    def create_token(user):
        """Crea un nuevo token de verificación para un usuario"""
        # Eliminar tokens anteriores si existen
        EmailVerificationToken.objects.filter(user=user).delete()
        
        # Generar token seguro
        token = secrets.token_urlsafe(32)
        
        # Configurar expiración a 24 horas
        expires_at = timezone.now() + timezone.timedelta(hours=24)
        
        # Crear y guardar el token
        verification_token = EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        return verification_token