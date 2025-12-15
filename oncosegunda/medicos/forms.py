# medicos/forms.py
from django import forms
from .models import Medico, AsignacionCaso, InformeSegundaOpinion, ComentarioCaso

class MedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = [
            'nombres', 'apellidos', 'email_institucional', 'telefono',
            'especialidad', 'numero_colegiado', 'estado'
        ]
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class AsignacionCasoForm(forms.ModelForm):
    class Meta:
        model = AsignacionCaso
        fields = ['medico', 'solicitud', 'tipo_asignacion', 'prioridad']
        widgets = {
            'tipo_asignacion': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
        }

class InformeSegundaOpinionForm(forms.ModelForm):
    class Meta:
        model = InformeSegundaOpinion
        fields = [
            'diagnostico_principal', 'descripcion_diagnostico',
            'recomendaciones_tratamiento', 'pronostico', 'conclusiones',
            'estado_informe'
        ]
        widgets = {
            'descripcion_diagnostico': forms.Textarea(attrs={'rows': 4}),
            'recomendaciones_tratamiento': forms.Textarea(attrs={'rows': 4}),
            'pronostico': forms.Textarea(attrs={'rows': 3}),
            'conclusiones': forms.Textarea(attrs={'rows': 4}),
            'estado_informe': forms.Select(attrs={'class': 'form-select'}),
        }

class ComentarioCasoForm(forms.ModelForm):
    class Meta:
        model = ComentarioCaso
        fields = ['comentario', 'tipo_comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={'rows': 3}),
            'tipo_comentario': forms.Select(attrs={'class': 'form-select'}),
        }