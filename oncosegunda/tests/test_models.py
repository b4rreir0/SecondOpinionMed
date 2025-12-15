# tests/test_models.py
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from tests.factories import (
    UserFactory, PacienteFactory, MedicoFactory,
    SolicitudSegundaOpinionFactory, DocumentoPacienteFactory,
    AsignacionCasoFactory, InformeSegundaOpinionFactory
)

class PacienteModelTest(TestCase):
    def setUp(self):
        self.paciente = PacienteFactory()

    def test_paciente_creation(self):
        """Test que se crea correctamente un paciente"""
        self.assertIsNotNone(self.paciente.id)
        self.assertEqual(self.paciente.user.paciente, self.paciente)

    def test_paciente_properties(self):
        """Test de propiedades calculadas del paciente"""
        self.assertEqual(self.paciente.nombre_completo, f"{self.paciente.user.first_name} {self.paciente.user.last_name}")

        # Test edad
        expected_age = date.today().year - self.paciente.fecha_nacimiento.year
        self.assertEqual(self.paciente.edad, expected_age)

    def test_paciente_str(self):
        """Test del método __str__ del paciente"""
        expected = f"{self.paciente.nombre_completo} - {self.paciente.numero_documento}"
        self.assertEqual(str(self.paciente), expected)

class MedicoModelTest(TestCase):
    def setUp(self):
        self.medico = MedicoFactory()

    def test_medico_creation(self):
        """Test que se crea correctamente un médico"""
        self.assertIsNotNone(self.medico.id)
        self.assertEqual(self.medico.user.medico, self.medico)

    def test_medico_properties(self):
        """Test de propiedades calculadas del médico"""
        self.assertEqual(self.medico.nombre_completo, f"{self.medico.user.first_name} {self.medico.user.last_name}")
        self.assertEqual(self.medico.capacidad_disponible, self.medico.max_casos_simultaneos - self.medico.casos_actuales)

    def test_medico_str(self):
        """Test del método __str__ del médico"""
        expected = f"Dr./Dra. {self.medico.nombre_completo} - {self.medico.registro_medico}"
        self.assertEqual(str(self.medico), expected)

    def test_actualizar_casos(self):
        """Test del método actualizar_casos"""
        initial_count = self.medico.casos_actuales
        self.medico.actualizar_casos(2)
        self.assertEqual(self.medico.casos_actuales, initial_count + 2)
        self.assertEqual(self.medico.casos_revisados, initial_count + 2)

class SolicitudSegundaOpinionTest(TestCase):
    def setUp(self):
        self.solicitud = SolicitudSegundaOpinionFactory()

    def test_solicitud_creation(self):
        """Test que se crea correctamente una solicitud"""
        self.assertIsNotNone(self.solicitud.id)
        self.assertTrue(self.solicitud.codigo.startswith('OP-'))

    def test_determinar_especialidad(self):
        """Test del método determinar_especialidad"""
        self.solicitud.tipo_cancer = 'mama'
        self.solicitud.determinar_especialidad()
        self.assertEqual(self.solicitud.especialidad_requerida, 'Oncología Mamaria')

        self.solicitud.tipo_cancer = 'otros'
        self.solicitud.determinar_especialidad()
        self.assertEqual(self.solicitud.especialidad_requerida, 'Oncología General')

    def test_solicitud_str(self):
        """Test del método __str__ de la solicitud"""
        expected = f"{self.solicitud.codigo} - {self.solicitud.paciente.user.get_full_name()}"
        self.assertEqual(str(self.solicitud), expected)

class DocumentoPacienteTest(TestCase):
    def setUp(self):
        self.documento = DocumentoPacienteFactory()

    def test_documento_creation(self):
        """Test que se crea correctamente un documento"""
        self.assertIsNotNone(self.documento.id)
        self.assertTrue(self.documento.hash_archivo)

    def test_documento_str(self):
        """Test del método __str__ del documento"""
        expected = f"{self.documento.get_tipo_display()} - {self.documento.solicitud.codigo}"
        self.assertEqual(str(self.documento), expected)

class AsignacionCasoTest(TestCase):
    def setUp(self):
        self.asignacion = AsignacionCasoFactory()

    def test_asignacion_creation(self):
        """Test que se crea correctamente una asignación"""
        self.assertIsNotNone(self.asignacion.id)
        self.assertEqual(self.asignacion.estado, 'asignado')

    def test_asignacion_str(self):
        """Test del método __str__ de la asignación"""
        expected = f"{self.asignacion.solicitud.codigo} → Dr. {self.asignacion.medico.user.last_name}"
        self.assertEqual(str(self.asignacion), expected)

class InformeSegundaOpinionTest(TestCase):
    def setUp(self):
        self.informe = InformeSegundaOpinionFactory()

    def test_informe_creation(self):
        """Test que se crea correctamente un informe"""
        self.assertIsNotNone(self.informe.id)
        self.assertTrue(self.informe.codigo_informe.startswith('INF-'))

    def test_informe_str(self):
        """Test del método __str__ del informe"""
        expected = f"{self.informe.codigo_informe} - {self.informe.asignacion.solicitud.codigo}"
        self.assertEqual(str(self.informe), expected)

class ModuloSistemaTest(TestCase):
    def setUp(self):
        self.modulo = ModuloSistemaFactory()

    def test_modulo_creation(self):
        """Test que se crea correctamente un módulo"""
        self.assertIsNotNone(self.modulo.id)
        self.assertEqual(self.modulo.estado, 'activo')

    def test_activar_desactivar(self):
        """Test de métodos activar/desactivar"""
        self.modulo.desactivar()
        self.assertEqual(self.modulo.estado, 'inactivo')
        self.assertIsNotNone(self.modulo.fecha_desactivacion)

        self.modulo.activar()
        self.assertEqual(self.modulo.estado, 'activo')
        self.assertIsNone(self.modulo.fecha_desactivacion)

    def test_modulo_str(self):
        """Test del método __str__ del módulo"""
        expected = f"{self.modulo.nombre} v{self.modulo.version}"
        self.assertEqual(str(self.modulo), expected)