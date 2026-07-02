from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from medicos.models import Localidad, TipoCancer, Especialidad
import datetime


class PatientProfileForm(forms.Form):
    full_name = forms.CharField(max_length=255, label='Nombre completo', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre y Apellido'}))
    identity_card = forms.CharField(max_length=20, label='Carnet de identidad', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de carnet de identidad'}))
    # Nueva fecha de nacimiento para calcular edad automáticamente
    date_of_birth = forms.DateField(
        label='Fecha de nacimiento',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    # Campo edad - se calculará automáticamente desde date_of_birth si existe
    age = forms.IntegerField(label='Edad', validators=[MinValueValidator(0), MaxValueValidator(120)], widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 120}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}))
    phone = forms.CharField(max_length=30, label='Telefono', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+54 9 11 1234 5678'}))
    
    # Campos del representante (cuando no es el paciente)
    representative_name = forms.CharField(max_length=255, label='Nombre del representante', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre y apellido del representante'}))
    representative_identity_card = forms.CharField(max_length=20, label='Carnet de identidad del representante', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de carnet de identidad del representante'}))
    
    # Campos para el nuevo flujo
    is_patient_holder = forms.BooleanField(
        label='¿La segunda opinión es para usted? (El titular de la cuenta es el paciente)',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_patient_holder'})
    )
    responsible_declaration = forms.BooleanField(
        label='Declaración de responsabilidad',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_responsible_declaration'})
    )
    declaration = forms.BooleanField(
        label='Acepto la declaración',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_declaration'})
    )


def validate_diagnosis_date_not_future(value):
    """Valida que la fecha de diagnostico no sea futura"""
    if value and value > timezone.now().date():
        raise forms.ValidationError('La fecha de diagnostico no puede ser futura. Debe ser hoy o una fecha anterior.')
    return value


ESTADIO_CHOICES = [
    ('', 'Seleccione el estadio'),
    ('I', 'Estadio I'),
    ('II', 'Estadio II'),
    ('III', 'Estadio III'),
    ('IV', 'Estadio IV'),
    ('N/A', 'No aplica'),
]


class CaseDraftForm(forms.Form):
    diagnosis_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de diagnostico',
        validators=[validate_diagnosis_date_not_future]
    )
    # Tipo de cancer - obligatorio ya que es necesario para funcionalidades futuras
    tipo_cancer = forms.ModelChoiceField(
        queryset=TipoCancer.objects.filter(activo=True),
        required=True,
        label='Localización de la enfermedad',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Seleccione la localización de la enfermedad'
    )
    referring_institution = forms.CharField(max_length=255, label='Hospital que emitio el diagnostico', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del hospital que emitio el diagnostico'}))

    def clean_diagnosis_date(self):
        """Validacion adicional en clean para mayor seguridad"""
        diagnosis_date = self.cleaned_data.get('diagnosis_date')
        if diagnosis_date and diagnosis_date > timezone.now().date():
            raise forms.ValidationError('La fecha de diagnostico no puede ser futura. Debe ser hoy o una fecha anterior.')
        return diagnosis_date


class CaseDocumentForm(forms.Form):
    document = forms.FileField(label='Documento medico', widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    document_type = forms.ChoiceField(label='Tipo de documento', choices=(
        ('resumen_historia_clinica', 'Resumen de Historia Clinica'),
        ('resultado_laboratorios', 'Resultado de Laboratorios'),
        ('resultado_imagenologia', 'Resultado de Imagenologia'),
        ('imagenes', 'Imagenes'),
        ('resultado_biopsia', 'Resultado de Biopsia'),
        ('otros_documentos', 'Otros Documentos Relevantes'),
    ), widget=forms.Select(attrs={'class': 'form-select'}))


class ReviewConsentForm(forms.Form):
    explicit_consent = forms.BooleanField(label='Acepto el consentimiento informado', required=True,
                                          widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
