# pacientes/forms.py
from django import forms
from .models import Paciente, SolicitudSegundaOpinion, DocumentoClinico

class PacienteForm(forms.ModelForm):
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Paciente
        fields = [
            'nombres', 'apellidos', 'fecha_nacimiento', 'genero',
            'numero_identificacion', 'tipo_identificacion', 'telefono',
            'email', 'direccion', 'estado_civil', 'ocupacion'
        ]
        widgets = {
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-select'}),
            'estado_civil': forms.Select(attrs={'class': 'form-select'}),
        }

class SolicitudSegundaOpinionForm(forms.ModelForm):
    fecha_diagnostico = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = SolicitudSegundaOpinion
        fields = [
            'caso', 'motivo_solicitud', 'especialidad_solicitada',
            'urgencia', 'autorizacion_eps', 'numero_autorizacion',
            'medico_remitente', 'institucion_remitente', 'contacto_remitente'
        ]
        widgets = {
            'motivo_solicitud': forms.Textarea(attrs={'rows': 4}),
            'urgencia': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'autorizacion_eps': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DocumentoClinicoForm(forms.ModelForm):
    class Meta:
        model = DocumentoClinico
        fields = ['tipo', 'titulo', 'archivo', 'descripcion', 'confidencial']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'confidencial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }