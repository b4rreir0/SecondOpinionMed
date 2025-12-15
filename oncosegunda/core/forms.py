# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Especialidad, Institucion

class UsuarioRegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    tipo_usuario = forms.ChoiceField(
        choices=[
            ('paciente', 'Paciente'),
            ('medico', 'Médico'),
            ('admin', 'Administrador')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'tipo_usuario']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # Aquí podríamos guardar el tipo_usuario en un perfil extendido
        if commit:
            user.save()
        return user

class UsuarioLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )

class EspecialidadForm(forms.ModelForm):
    class Meta:
        model = Especialidad
        fields = ['nombre', 'descripcion', 'estado']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        fields = ['nombre', 'tipo', 'direccion', 'telefono', 'email', 'estado']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }