from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.db import transaction

from .models import CustomUser, PatientProfile, DoctorProfile, EmailVerificationToken


class EmailService:
    """
    Servicio de envío de emails.
    
    Encapsula la lógica de envío de emails de verificación y notificaciones.
    """
    
    @staticmethod
    def send_verification_email(user, request):
        """
        Envía email de verificación al usuario.
        
        Args:
            user (CustomUser): Usuario a verificar
            request: Objeto de request para construir URLs absolutas
        """
        # Crear o actualizar token de verificación
        verification_token = EmailVerificationToken.create_token(user)
        
        # Construir URL de verificación
        verification_url = request.build_absolute_uri(
            reverse('auth:verify_email', kwargs={'token': verification_token.token})
        )
        
        # Preparar email
        subject = '🏥 Confirma tu Email - Segunda Opinión Médica'
        message = f"""
        Hola {user.email},
        
        Gracias por registrarte en Segunda Opinión Médica.
        
        Para activar tu cuenta, haz clic en el siguiente enlace:
        {verification_url}
        
        Este enlace expira en 24 horas.
        
        Si no solicitaste este registro, ignora este email.
        
        Saludos,
        El equipo de Segunda Opinión Médica
        """
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">🏥 Confirma tu Email</h2>
                    <p>Hola <strong>{user.email}</strong>,</p>
                    <p>Gracias por registrarte en <strong>Segunda Opinión Médica</strong>.</p>
                    <p>Para activar tu cuenta, haz clic en el botón de abajo:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #0066cc; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Verificar Email
                        </a>
                    </div>
                    <p style="font-size: 12px; color: #999;">
                        Este enlace expira en 24 horas.<br>
                        Si no solicitaste este registro, ignora este email.
                    </p>
                    <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
                    <p style="font-size: 12px; color: #999;">
                        El equipo de Segunda Opinión Médica
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Enviar email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@secondopinionmedica.com',
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            return True
        except Exception as e:
            print(f"Error al enviar email de verificación: {e}")
            return False
    
    @staticmethod
    def verify_email_token(token):
        """
        Verifica un token de email y activa la cuenta del usuario.
        
        Args:
            token (str): Token de verificación
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            verification_token = EmailVerificationToken.objects.get(token=token)
            
            # Verificar que el token sea válido
            if not verification_token.is_valid():
                return False, "El token ha expirado o ya fue utilizado."
            
            # Activar usuario y marcar email como verificado
            user = verification_token.user
            user.is_active = True
            user.email_verified = True
            user.save()
            
            # Marcar token como usado
            verification_token.is_used = True
            verification_token.used_at = timezone.now()
            verification_token.save()
            
            return True, "¡Email verificado exitosamente! Tu cuenta está activa."
            
        except EmailVerificationToken.DoesNotExist:
            return False, "Token de verificación inválido."
        except Exception as e:
            return False, f"Error al verificar el email: {str(e)}"


class AuthenticationService:
    """
    Servicio de autenticación centralizado.
    
    Encapsula la lógica de autenticación y redirección según el rol.
    Mantiene las vistas delgadas y reutilizable para testing.
    """
    
    @staticmethod
    def authenticate_user(email, password):
        """
        Autentica un usuario con email y contraseña.
        
        Returns:
            CustomUser or None: Usuario autenticado o None si falla
        """
        user = authenticate(username=email, password=password)
        return user
    
    @staticmethod
    def get_redirect_url(user):
        """
        Determina la URL de redirección según el rol del usuario.
        
        Args:
            user (CustomUser): Usuario autenticado
            
        Returns:
            str: URL de redirección
        """
        if user.is_doctor():
            return '/doctors/dashboard/'
        elif user.is_patient():
            return '/patients/dashboard/'
        return '/'
    
    @staticmethod
    def get_user_role_display(user):
        """Retorna el nombre del rol en formato legible"""
        return user.get_role_display()


class PatientRegistrationService:
    """
    Servicio de registro de pacientes.
    
    Orquesta la creación del usuario CustomUser y su perfil PatientProfile.
    Garantiza transaccionalidad y validación.
    """
    
    @staticmethod
    @transaction.atomic
    def register_patient(email, password, full_name, identity_document, phone_number):
        """
        Registra un nuevo paciente en el sistema.
        
        Args:
            email (str): Email único
            password (str): Contraseña en texto plano
            full_name (str): Nombre completo
            identity_document (str): Cédula o documento de identidad
            phone_number (str): Teléfono de contacto
            
        Returns:
            tuple: (CustomUser, PatientProfile) o raise ValidationError
            
        Raises:
            ValidationError: Si ya existe un usuario con ese email
        """
        # Verificar que el email no exista
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("El email ya está registrado.")
        
        if PatientProfile.objects.filter(identity_document=identity_document).exists():
            raise ValidationError("El documento de identidad ya está registrado.")
        
        # Crear usuario (inicialmente inactivo hasta verificar email)
        user = CustomUser.objects.create_user(
            username=email,  # Username = email para unicidad
            email=email,
            password=password,
            role='patient',
            is_active=False,  # Inactivo hasta verificar email
            email_verified=False
        )
        
        # Crear perfil de paciente
        patient_profile = PatientProfile.objects.create(
            user=user,
            full_name=full_name,
            identity_document=identity_document,
            phone_number=phone_number
        )
        
        return user, patient_profile


class DoctorRegistrationService:
    """
    Servicio de registro de médicos.
    
    Orquesta la creación del usuario CustomUser y su perfil DoctorProfile.
    Garantiza transaccionalidad y validación.
    """
    
    @staticmethod
    @transaction.atomic
    def register_doctor(email, password, full_name, medical_license, specialty, phone_number, institution=''):
        """
        Registra un nuevo médico en el sistema.
        
        Args:
            email (str): Email único
            password (str): Contraseña en texto plano
            full_name (str): Nombre completo
            medical_license (str): Número de licencia médica
            specialty (str): Especialidad médica
            phone_number (str): Teléfono profesional
            institution (str): Institución (opcional)
            
        Returns:
            tuple: (CustomUser, DoctorProfile) o raise ValidationError
            
        Raises:
            ValidationError: Si ya existe un usuario con ese email o licencia
        """
        # Verificar que el email no exista
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("El email ya está registrado.")
        
        if DoctorProfile.objects.filter(medical_license=medical_license).exists():
            raise ValidationError("El número de licencia médica ya está registrado.")
        
        # Crear usuario
        user = CustomUser.objects.create_user(
            username=email,
            email=email,
            password=password,
            role='doctor',
            is_active=True
        )
        
        # Crear perfil de médico
        doctor_profile = DoctorProfile.objects.create(
            user=user,
            full_name=full_name,
            medical_license=medical_license,
            specialty=specialty,
            phone_number=phone_number,
            institution=institution
        )
        
        return user, doctor_profile
