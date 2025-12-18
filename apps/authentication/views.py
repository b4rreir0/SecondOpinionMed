from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect

from .forms import LoginForm, PatientRegistrationForm
from .services import (
    AuthenticationService,
    PatientRegistrationService,
    EmailService
)


class LoginView(View):
    """
    Vista de inicio de sesión.
    
    Realiza autenticación y redirección dinámica según el rol del usuario.
    Utiliza la capa de servicios para mantener la vista delgada.
    """
    template_name = 'auth/login.html'
    
    def get(self, request):
        """Muestra el formulario de login"""
        if request.user.is_authenticated:
            # Si ya está autenticado, redirige a su dashboard
            return redirect(AuthenticationService.get_redirect_url(request.user))
        
        form = LoginForm()
        context = {'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Procesa el login y redirige según el rol"""
        form = LoginForm(request.POST)
        
        if form.is_valid():
            user = form.get_user()
            if user and user.is_active:
                # Iniciar sesión
                login(request, user)
                
                # Obtener URL de redirección según el rol
                redirect_url = AuthenticationService.get_redirect_url(user)
                return redirect(redirect_url)
        
        context = {'form': form}
        return render(request, self.template_name, context)


class LogoutView(View):
    """Vista para cerrar sesión"""
    
    def post(self, request):
        """Cierra la sesión del usuario"""
        logout(request)
        return redirect('/')


class PatientRegistrationView(View):
    """
    Vista de registro de pacientes.
    
    Captura datos del paciente y orquesta la creación del usuario
    y su perfil utilizando PatientRegistrationService.
    """
    template_name = 'auth/register_patient.html'
    
    def get(self, request):
        """Muestra el formulario de registro"""
        if request.user.is_authenticated:
            return redirect(AuthenticationService.get_redirect_url(request.user))
        
        form = PatientRegistrationForm()
        context = {'form': form, 'role': 'patient'}
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Procesa el registro y crea el usuario"""
        form = PatientRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                user, patient_profile = PatientRegistrationService.register_patient(
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    full_name=form.cleaned_data['full_name'],
                    identity_document=form.cleaned_data['identity_document'],
                    phone_number=form.cleaned_data['phone_number']
                )
                
                # Enviar email de verificación
                email_sent = EmailService.send_verification_email(user, request)
                
                if email_sent:
                    # Redirigir a página de confirmación (pasar email como query string)
                    return redirect(f"{reverse('auth:verification_pending')}?email={user.email}")
                else:
                    # Si no se puede enviar el email, mostrar error
                    form.add_error(None, "No pudimos enviar el email de verificación. Por favor intenta más tarde.")
                
            except ValidationError as e:
                form.add_error(None, str(e))
        
        context = {'form': form, 'role': 'patient'}
        return render(request, self.template_name, context)


class DoctorRegistrationView(View):
    """
    Vista de registro de médicos.
    
    NOTA: Los médicos serán creados por administradores en el futuro.
    Esta vista se mantiene para referencia y será implementada posteriormente.
    """
    def get(self, request):
        return redirect('/')


class RegistrationChoiceView(View):
    """
    Vista de elección de tipo de registro.
    
    NOTA: Previamente permitía elegir entre Paciente y Médico.
    Ahora solo se permiten registros de pacientes.
    Esta vista se mantiene para referencia y redirige a registro de pacientes.
    """
    def get(self, request):
        return redirect('auth:register_patient')


class VerificationPendingView(View):
    """
    Vista que muestra el estado de pendiente de verificación de email.
    """
    template_name = 'auth/verification_pending.html'
    
    def get(self, request):
        email = request.GET.get('email', '')
        context = {'email': email}
        return render(request, self.template_name, context)


class VerifyEmailView(View):
    """
    Vista para verificar el email del usuario mediante el token.
    """
    template_name = 'auth/email_verified.html'
    
    def get(self, request, token):
        success, message = EmailService.verify_email_token(token)
        context = {
            'success': success,
            'message': message
        }
        return render(request, self.template_name, context)
