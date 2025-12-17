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
            'numero_documento', 'tipo_documento', 'telefono',
            'email_alternativo', 'estado_civil'
        ]
        widgets = {
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'estado_civil': forms.Select(attrs={'class': 'form-select'}),
        }

class SolicitudSegundaOpinionForm(forms.ModelForm):
    fecha_diagnostico = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = SolicitudSegundaOpinion
        fields = [
            'motivo_solicitud', 'especialidad_solicitada',
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

class CasoClinicoForm(forms.Form):
    """Formulario genérico para casos clínicos"""
    titulo = forms.CharField(max_length=200, required=True)
    descripcion = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), required=False)

class AntecedenteMedicoForm(forms.Form):
    """Formulario genérico para antecedentes médicos"""
    tipo = forms.CharField(max_length=100, required=True)
    descripcion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)