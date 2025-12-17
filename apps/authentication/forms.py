from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .models import CustomUser, PatientProfile, DoctorProfile


class LoginForm(forms.Form):
    """
    Formulario de inicio de sesión.
    
    Acepta email y contraseña. El token CSRF se incluye automáticamente
    en el template mediante {% csrf_token %}.
    """
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña',
            'autocomplete': 'current-password'
        })
    )
    
    def clean(self):
        """Valida que las credenciales sean correctas"""
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            # Authenticate usa 'username', que configuramos como email
            self.user = authenticate(username=email, password=password)
            if self.user is None:
                raise ValidationError("Email o contraseña incorrectos.")
        
        return cleaned_data
    
    def get_user(self):
        """Retorna el usuario autenticado"""
        return getattr(self, 'user', None)


class PatientRegistrationForm(forms.Form):
    """
    Formulario de registro de pacientes.
    
    Captura datos personales y de identificación necesarios para crear
    un CustomUser y su PatientProfile asociado.
    """
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )
    password_confirm = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme su contraseña',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )
    full_name = forms.CharField(
        label="Nombre Completo",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre y Apellidos',
            'autocomplete': 'name'
        })
    )
    identity_document = forms.CharField(
        label="Cédula de Identidad / Pasaporte",
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1234567890',
            'autocomplete': 'off'
        })
    )
    phone_number = forms.CharField(
        label="Número de Teléfono",
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+34 912 34 56 78',
            'autocomplete': 'tel',
            'type': 'tel'
        })
    )
    consent = forms.BooleanField(
        label="Acepto los Términos y Condiciones y la Política de Privacidad",
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    def clean_email(self):
        """Valida que el email sea único"""
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Este email ya está registrado.")
        return email
    
    def clean_identity_document(self):
        """Valida que el documento sea único"""
        identity_document = self.cleaned_data['identity_document']
        if PatientProfile.objects.filter(identity_document=identity_document).exists():
            raise ValidationError("Este documento de identidad ya está registrado.")
        return identity_document
    
    def clean(self):
        """Valida que las contraseñas coincidan"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError("Las contraseñas no coinciden.")
        
        if not cleaned_data.get('consent'):
            raise ValidationError("Debe aceptar los Términos y Condiciones para continuar.")
        
        return cleaned_data


class DoctorRegistrationForm(forms.Form):
    """
    Formulario de registro de médicos.
    
    Captura datos profesionales necesarios para crear un CustomUser
    y su DoctorProfile asociado.
    """
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )
    password_confirm = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme su contraseña',
            'autocomplete': 'new-password'
        }),
        min_length=8
    )
    full_name = forms.CharField(
        label="Nombre Completo",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dr. Nombre Completo',
            'autocomplete': 'name'
        })
    )
    medical_license = forms.CharField(
        label="Número de Licencia Médica",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de colegiación',
            'autocomplete': 'off'
        })
    )
    specialty = forms.ChoiceField(
        label="Especialidad",
        choices=DoctorProfile.SPECIALTY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    phone_number = forms.CharField(
        label="Número de Teléfono Profesional",
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+34 912 34 56 78',
            'autocomplete': 'tel',
            'type': 'tel'
        })
    )
    institution = forms.CharField(
        label="Institución / Clínica",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de la institución (opcional)'
        })
    )
    consent = forms.BooleanField(
        label="Acepto los Términos y Condiciones y la Política de Privacidad",
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_email(self):
        """Valida que el email sea único"""
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Este email ya está registrado.")
        return email
    
    def clean_medical_license(self):
        """Valida que la licencia sea única"""
        medical_license = self.cleaned_data['medical_license']
        if DoctorProfile.objects.filter(medical_license=medical_license).exists():
            raise ValidationError("Este número de licencia médica ya está registrado.")
        return medical_license
    
    def clean(self):
        """Valida que las contraseñas coincidan"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError("Las contraseñas no coinciden.")
        
        if not cleaned_data.get('consent'):
            raise ValidationError("Debe aceptar los Términos y Condiciones para continuar.")
        
        return cleaned_data
