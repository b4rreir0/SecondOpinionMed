# tests/test_services.py
import pytest
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch, MagicMock
from tests.factories import (
    UserFactory, PacienteFactory, MedicoFactory,
    SolicitudSegundaOpinionFactory, AsignacionCasoFactory
)
from core.services import (
    ServicioAuditoria, ServicioAsignacion, ServicioNotificaciones,
    ServicioValidacion
)

class ServicioAuditoriaTest(TestCase):
    def setUp(self):
        self.servicio = ServicioAuditoria()
        self.user = UserFactory()

    def test_registrar_accion(self):
        """Test del registro de acciones de auditoría"""
        with patch('core.services.Auditoria.objects.create') as mock_create:
            self.servicio.registrar_accion(
                usuario=self.user,
                accion='login',
                detalles={'ip': '192.168.1.1'},
                modulo='public'
            )

            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            self.assertEqual(call_args['usuario'], self.user)
            self.assertEqual(call_args['accion'], 'login')
            self.assertEqual(call_args['detalles'], {'ip': '192.168.1.1'})
            self.assertEqual(call_args['modulo'], 'public')

class ServicioAsignacionTest(TestCase):
    def setUp(self):
        self.servicio = ServicioAsignacion()
        self.solicitud = SolicitudSegundaOpinionFactory()

    def test_asignar_caso_round_robin(self):
        """Test de asignación round-robin"""
        # Crear médicos disponibles
        medicos = [MedicoFactory(especialidad='Oncología General') for _ in range(3)]

        # Asignar casos para probar round-robin
        asignacion1 = self.servicio.asignar_caso(self.solicitud)
        asignacion2 = self.servicio.asignar_caso(SolicitudSegundaOpinionFactory())

        # Verificar que se asignaron médicos diferentes
        self.assertNotEqual(asignacion1.medico, asignacion2.medico)
        self.assertIn(asignacion1.medico, medicos)
        self.assertIn(asignacion2.medico, medicos)

    def test_asignar_caso_sin_medicos_disponibles(self):
        """Test cuando no hay médicos disponibles"""
        # Crear médico con capacidad llena
        medico = MedicoFactory(max_casos_simultaneos=0)

        with self.assertRaises(ValueError):
            self.servicio.asignar_caso(self.solicitud)

    def test_reasignar_caso(self):
        """Test de reasignación de caso"""
        asignacion = AsignacionCasoFactory()
        nuevo_medico = MedicoFactory(especialidad='Oncología General')

        with patch('core.services.ServicioAuditoria') as mock_auditoria:
            resultado = self.servicio.reasignar_caso(asignacion, nuevo_medico, 'Motivo de prueba')

            self.assertEqual(resultado.medico, nuevo_medico)
            self.assertEqual(resultado.estado, 'reasignado')
            mock_auditoria.return_value.registrar_accion.assert_called()

class ServicioNotificacionesTest(TestCase):
    def setUp(self):
        self.servicio = ServicioNotificaciones()
        self.paciente = PacienteFactory()
        self.medico = MedicoFactory()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_enviar_notificacion_paciente(self):
        """Test de envío de notificación a paciente"""
        with patch('core.services.send_mail') as mock_send:
            self.servicio.enviar_notificacion_paciente(
                self.paciente,
                'solicitud_creada',
                {'codigo': 'OP-001'}
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            self.assertIn(self.paciente.user.email, call_args[0][3])
            self.assertIn('OP-001', call_args[0][1])

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_enviar_notificacion_medico(self):
        """Test de envío de notificación a médico"""
        with patch('core.services.send_mail') as mock_send:
            self.servicio.enviar_notificacion_medico(
                self.medico,
                'caso_asignado',
                {'codigo': 'OP-001'}
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            self.assertIn(self.medico.user.email, call_args[0][3])
            self.assertIn('OP-001', call_args[0][1])

class ServicioValidacionTest(TestCase):
    def setUp(self):
        self.servicio = ServicioValidacion()

    def test_validar_archivo_pdf(self):
        """Test de validación de archivo PDF"""
        # Crear archivo PDF mock
        mock_file = MagicMock()
        mock_file.name = 'documento.pdf'
        mock_file.size = 1024 * 1024  # 1MB

        # Validar
        resultado = self.servicio.validar_archivo(mock_file, 'pdf')
        self.assertTrue(resultado['valido'])
        self.assertEqual(resultado['tipo'], 'pdf')

    def test_validar_archivo_tamano_excedido(self):
        """Test de validación con archivo demasiado grande"""
        mock_file = MagicMock()
        mock_file.name = 'documento.pdf'
        mock_file.size = 50 * 1024 * 1024  # 50MB

        resultado = self.servicio.validar_archivo(mock_file, 'pdf')
        self.assertFalse(resultado['valido'])
        self.assertIn('tamaño', resultado['errores'][0])

    def test_validar_archivo_tipo_incorrecto(self):
        """Test de validación con tipo de archivo incorrecto"""
        mock_file = MagicMock()
        mock_file.name = 'documento.exe'
        mock_file.size = 1024

        resultado = self.servicio.validar_archivo(mock_file, 'pdf')
        self.assertFalse(resultado['valido'])
        self.assertIn('tipo', resultado['errores'][0])

    def test_validar_datos_paciente(self):
        """Test de validación de datos de paciente"""
        datos_validos = {
            'numero_documento': '12345678',
            'tipo_documento': 'cedula',
            'fecha_nacimiento': date.today() - timedelta(days=365*25),
            'telefono': '+593987654321'
        }

        resultado = self.servicio.validar_datos_paciente(datos_validos)
        self.assertTrue(resultado['valido'])

    def test_validar_datos_paciente_edad_invalida(self):
        """Test de validación con edad inválida"""
        datos_invalidos = {
            'numero_documento': '12345678',
            'tipo_documento': 'cedula',
            'fecha_nacimiento': date.today() - timedelta(days=365*5),  # 5 años
            'telefono': '+593987654321'
        }

        resultado = self.servicio.validar_datos_paciente(datos_invalidos)
        self.assertFalse(resultado['valido'])
        self.assertIn('edad', resultado['errores'][0])