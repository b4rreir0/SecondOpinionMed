# tests/test_forms.py
import pytest
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from tests.factories import UserFactory, PacienteFactory, MedicoFactory, SolicitudSegundaOpinionFactory
from public.forms import PacienteRegistrationForm, ContactForm
from pacientes.forms import SolicitudPaso1Form, SolicitudPaso2Form, DocumentoForm, PerfilPacienteForm
from medicos.forms import PerfilMedicoForm, ValidarDocumentacionForm, InformeForm

class PublicFormsTest(TestCase):
    def test_paciente_registration_form_valid(self):
        """Test del formulario de registro de paciente - válido"""
        data = {
            'username': 'paciente_test',
            'email': 'paciente@test.com',
            'password1': 'password123',
            'password2': 'password123',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'numero_documento': '12345678',
            'tipo_documento': 'cedula',
            'fecha_nacimiento': '1980-01-01',
            'telefono': '+593987654321',
            'direccion': 'Dirección de prueba'
        }

        form = PacienteRegistrationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_paciente_registration_form_invalid_password(self):
        """Test del formulario de registro - contraseñas no coinciden"""
        data = {
            'username': 'paciente_test',
            'email': 'paciente@test.com',
            'password1': 'password123',
            'password2': 'password456',
            'first_name': 'Juan',
            'last_name': 'Pérez'
        }

        form = PacienteRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_contact_form_valid(self):
        """Test del formulario de contacto - válido"""
        data = {
            'nombre': 'Juan Pérez',
            'email': 'juan@test.com',
            'asunto': 'Consulta general',
            'mensaje': 'Mensaje de prueba'
        }

        form = ContactForm(data=data)
        self.assertTrue(form.is_valid())

class PacienteFormsTest(TestCase):
    def setUp(self):
        self.paciente = PacienteFactory()

    def test_solicitud_paso1_form_valid(self):
        """Test del formulario de solicitud paso 1 - válido"""
        data = {
            'tipo_cancer': 'mama',
            'descripcion_caso': 'Descripción detallada del caso',
            'urgencia': 'normal',
            'consentimiento_informado': True
        }

        form = SolicitudPaso1Form(data=data)
        self.assertTrue(form.is_valid())

    def test_solicitud_paso1_form_missing_consent(self):
        """Test del formulario de solicitud paso 1 - consentimiento faltante"""
        data = {
            'tipo_cancer': 'mama',
            'descripcion_caso': 'Descripción detallada del caso',
            'urgencia': 'normal',
            'consentimiento_informado': False
        }

        form = SolicitudPaso1Form(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('consentimiento_informado', form.errors)

    def test_solicitud_paso2_form_valid(self):
        """Test del formulario de solicitud paso 2 - válido"""
        data = {
            'sintomas': 'Síntomas detallados',
            'tratamientos_previos': 'Tratamientos anteriores',
            'medicamentos_actuales': 'Medicamentos actuales',
            'alergias': 'Ninguna',
            'condiciones_medicas': 'Condiciones médicas'
        }

        form = SolicitudPaso2Form(data=data)
        self.assertTrue(form.is_valid())

    def test_documento_form_valid_pdf(self):
        """Test del formulario de documento - PDF válido"""
        pdf_file = SimpleUploadedFile(
            "documento.pdf",
            b"contenido del pdf",
            content_type="application/pdf"
        )

        data = {'tipo_documento': 'historia_clinica'}
        files = {'archivo': pdf_file}

        form = DocumentoForm(data=data, files=files)
        self.assertTrue(form.is_valid())

    def test_documento_form_invalid_type(self):
        """Test del formulario de documento - tipo inválido"""
        exe_file = SimpleUploadedFile(
            "documento.exe",
            b"contenido del exe",
            content_type="application/octet-stream"
        )

        data = {'tipo_documento': 'historia_clinica'}
        files = {'archivo': exe_file}

        form = DocumentoForm(data=data, files=files)
        self.assertFalse(form.is_valid())
        self.assertIn('archivo', form.errors)

    def test_perfil_paciente_form_valid(self):
        """Test del formulario de perfil de paciente - válido"""
        data = {
            'telefono': '+593987654321',
            'direccion': 'Nueva dirección',
            'contacto_emergencia_nombre': 'María Pérez',
            'contacto_emergencia_telefono': '+593987654322'
        }

        form = PerfilPacienteForm(data=data, instance=self.paciente)
        self.assertTrue(form.is_valid())

class MedicoFormsTest(TestCase):
    def setUp(self):
        self.medico = MedicoFactory()

    def test_perfil_medico_form_valid(self):
        """Test del formulario de perfil de médico - válido"""
        data = {
            'registro_medico': '12345',
            'especialidad': 'Oncología General',
            'institucion': 'Hospital Central',
            'telefono': '+593987654321',
            'max_casos_simultaneos': 5
        }

        form = PerfilMedicoForm(data=data, instance=self.medico)
        self.assertTrue(form.is_valid())

    def test_validar_documentacion_form_valid(self):
        """Test del formulario de validación de documentación - válido"""
        data = {
            'documentacion_completa': True,
            'observaciones': 'Documentación completa y clara'
        }

        form = ValidarDocumentacionForm(data=data)
        self.assertTrue(form.is_valid())

    def test_informe_form_valid(self):
        """Test del formulario de informe - válido"""
        data = {
            'diagnostico': 'Diagnóstico detallado',
            'recomendaciones': 'Recomendaciones específicas',
            'tratamiento_sugerido': 'Tratamiento recomendado',
            'seguimiento_requerido': True,
            'observaciones': 'Observaciones adicionales'
        }

        form = InformeForm(data=data)
        self.assertTrue(form.is_valid())

    def test_informe_form_missing_diagnostico(self):
        """Test del formulario de informe - diagnóstico faltante"""
        data = {
            'recomendaciones': 'Recomendaciones específicas',
            'tratamiento_sugerido': 'Tratamiento recomendado',
            'seguimiento_requerido': True
        }

        form = InformeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('diagnostico', form.errors)