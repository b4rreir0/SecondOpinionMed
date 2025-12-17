# administracion/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import ConfiguracionSistema, Administrador

class AdministradorForm(forms.ModelForm):
    class Meta:
        model = Administrador
        fields = [
            'nombres', 'apellidos', 'email_institucional', 'telefono',
            'departamento', 'cargo', 'estado'
        ]
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class ConfiguracionSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSistema
        fields = ['clave', 'valor', 'tipo', 'descripcion', 'categoria']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'valor': forms.Textarea(attrs={'rows': 3}),
        }

class UsuarioCreacionForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user