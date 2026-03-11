from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from medicos.models import Localidad, TipoCancer, Especialidad


class PatientProfileForm(forms.Form):
    full_name = forms.CharField(max_length=255, label='Nombre completo', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre y Apellido'}))
    age = forms.IntegerField(label='Edad', validators=[MinValueValidator(0), MaxValueValidator(120)], widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 120}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}))
    phone = forms.CharField(max_length=30, label='Telefono', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+54 9 11 1234 5678'}))
    medical_history = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False, label='Enfermedades que padecen')
    current_medications = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, label='Medicamentos actuales')
    known_allergies = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, label='Alergias conocidas')


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
    primary_diagnosis = forms.CharField(max_length=255, label='Diagnostico primario', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Adenocarcinoma de pulmon'}))
    diagnosis_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), 
        label='Fecha de diagnostico',
        validators=[validate_diagnosis_date_not_future]
    )
    # Tipo de cancer - obligatorio ya que es necesario para funcionalidades futuras
    tipo_cancer = forms.ModelChoiceField(
        queryset=TipoCancer.objects.filter(activo=True),
        required=True,
        label='¿Dónde está localizada la enfermedad?',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Seleccione la localización de la enfermedad'
    )
    # Estadio del cancer - opcional ya que se obtiene de los documentos
    estadio = forms.ChoiceField(
        choices=ESTADIO_CHOICES,
        required=False,
        label='Estadio del Cancer',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    referring_institution = forms.CharField(max_length=255, label='Hospital que emitio el diagnostico', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del hospital que emitio el diagnostico'}))
    main_symptoms = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), label='Sintomas principales')

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
