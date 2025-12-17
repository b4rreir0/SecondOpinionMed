from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


class PatientProfileForm(forms.Form):
    full_name = forms.CharField(max_length=255, label='Nombre completo')
    age = forms.IntegerField(label='Edad', validators=[MinValueValidator(0), MaxValueValidator(120)])
    email = forms.EmailField(label='Email')
    phone = forms.CharField(max_length=30, label='Teléfono')
    medical_history = forms.CharField(widget=forms.Textarea, required=False, label='Historial médico')
    current_medications = forms.CharField(widget=forms.Textarea, required=False, label='Medicamentos actuales')
    known_allergies = forms.CharField(widget=forms.Textarea, required=False, label='Alergias conocidas')


class CaseDraftForm(forms.Form):
    primary_diagnosis = forms.CharField(max_length=255, label='Diagnóstico primario')
    diagnosis_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Fecha de diagnóstico')
    referring_institution = forms.CharField(max_length=255, label='Institución que refiere')
    main_symptoms = forms.CharField(widget=forms.Textarea, label='Síntomas principales')


class CaseDocumentForm(forms.Form):
    document = forms.FileField(label='Documento médico')
    document_type = forms.ChoiceField(label='Tipo de documento', choices=(
        ('diagnostic_report', 'Informe Diagnóstico'),
        ('imaging', 'Imágenes Diagnósticas'),
        ('lab_results', 'Resultados de Laboratorio'),
        ('other', 'Otro'),
    ))


class ReviewConsentForm(forms.Form):
    explicit_consent = forms.BooleanField(label='Acepto el consentimiento informado')
