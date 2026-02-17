from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from medicos.models import Localidad


class PatientProfileForm(forms.Form):
    full_name = forms.CharField(max_length=255, label='Nombre completo', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre y Apellido'}))
    age = forms.IntegerField(label='Edad', validators=[MinValueValidator(0), MaxValueValidator(120)], widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 120}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}))
    phone = forms.CharField(max_length=30, label='Teléfono', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+54 9 11 1234 5678'}))
    medical_history = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False, label='Historial médico')
    current_medications = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, label='Medicamentos actuales')
    known_allergies = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, label='Alergias conocidas')


def validate_diagnosis_date_not_future(value):
    """Valida que la fecha de diagnóstico no sea futura"""
    if value and value > timezone.now().date():
        raise forms.ValidationError('La fecha de diagnóstico no puede ser futura. Debe ser hoy o una fecha anterior.')
    return value


class CaseDraftForm(forms.Form):
    primary_diagnosis = forms.CharField(max_length=255, label='Diagnóstico primario', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Adenocarcinoma de pulmón'}))
    diagnosis_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), 
        label='Fecha de diagnóstico',
        validators=[validate_diagnosis_date_not_future]
    )
    referring_institution = forms.CharField(max_length=255, label='Institución que refiere', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la institución que remite'}))
    main_symptoms = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), label='Síntomas principales')
    localidad = forms.ModelChoiceField(queryset=Localidad.objects.all(), required=False, label='Localidad', widget=forms.Select(attrs={'class': 'form-select'}))

    def clean_diagnosis_date(self):
        """Validación adicional en clean para mayor seguridad"""
        diagnosis_date = self.cleaned_data.get('diagnosis_date')
        if diagnosis_date and diagnosis_date > timezone.now().date():
            raise forms.ValidationError('La fecha de diagnóstico no puede ser futura. Debe ser hoy o una fecha anterior.')
        return diagnosis_date


class CaseDocumentForm(forms.Form):
    document = forms.FileField(label='Documento médico', widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    document_type = forms.ChoiceField(label='Tipo de documento', choices=(
        ('diagnostic_report', 'Informe Diagnóstico'),
        ('imaging', 'Imágenes Diagnósticas'),
        ('lab_results', 'Resultados de Laboratorio'),
        ('other', 'Otro'),
    ), widget=forms.Select(attrs={'class': 'form-select'}))


class ReviewConsentForm(forms.Form):
    explicit_consent = forms.BooleanField(label='Acepto el consentimiento informado', required=True,
                                          widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
