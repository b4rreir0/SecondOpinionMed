# tests/test_views.py
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tests.factories import (
    UserFactory, PacienteFactory, MedicoFactory,
    SolicitudSegundaOpinionFactory, AsignacionCasoFactory
)

User = get_user_model()

class PublicViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_landing_page(self):
        """Test de la página de inicio"""
        response = self.client.get(reverse('public:landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'public/landing.html')

    def test_login_view_get(self):
        """Test de la vista de login - GET"""
        response = self.client.get(reverse('public:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'public/login.html')

    def test_login_view_post_success(self):
        """Test de login exitoso"""
        user = UserFactory()
        user.set_password('password123')
        user.save()

        response = self.client.post(reverse('public:login'), {
            'username': user.username,
            'password': 'password123'
        })

        self.assertEqual(response.status_code, 302)  # Redirect

    def test_register_view_get(self):
        """Test de la vista de registro - GET"""
        response = self.client.get(reverse('public:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'public/register.html')

class PacienteViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.paciente = PacienteFactory()
        self.client.login(username=self.paciente.user.username, password='password123')

    def test_dashboard_paciente(self):
        """Test del dashboard del paciente"""
        response = self.client.get(reverse('pacientes:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pacientes/dashboard.html')

    def test_nueva_solicitud_paso1_get(self):
        """Test de nueva solicitud paso 1 - GET"""
        response = self.client.get(reverse('pacientes:nueva_solicitud_paso1'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pacientes/nueva_solicitud_paso1.html')

    def test_nueva_solicitud_paso1_post(self):
        """Test de nueva solicitud paso 1 - POST"""
        data = {
            'tipo_cancer': 'mama',
            'descripcion_caso': 'Descripción de prueba',
            'urgencia': 'normal'
        }
        response = self.client.post(reverse('pacientes:nueva_solicitud_paso1'), data)
        self.assertEqual(response.status_code, 302)  # Redirect to paso 2

    def test_mis_solicitudes(self):
        """Test de la vista de mis solicitudes"""
        SolicitudSegundaOpinionFactory(paciente=self.paciente)
        response = self.client.get(reverse('pacientes:mis_solicitudes'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pacientes/mis_solicitudes.html')
        self.assertContains(response, 'OP-')  # Código de solicitud

class MedicoViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.medico = MedicoFactory()
        self.client.login(username=self.medico.user.username, password='password123')

    def test_dashboard_medico(self):
        """Test del dashboard del médico"""
        response = self.client.get(reverse('medicos:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'medicos/dashboard.html')

    def test_casos_asignados(self):
        """Test de la vista de casos asignados"""
        AsignacionCasoFactory(medico=self.medico)
        response = self.client.get(reverse('medicos:casos_asignados'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'medicos/casos_asignados.html')

    def test_revisar_caso(self):
        """Test de revisión de caso"""
        asignacion = AsignacionCasoFactory(medico=self.medico)
        response = self.client.get(reverse('medicos:revisar_caso', args=[asignacion.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'medicos/revisar_caso.html')

class AdministracionViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=self.admin.username, password='password123')

    def test_dashboard_admin(self):
        """Test del dashboard de administración"""
        response = self.client.get(reverse('administracion:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'administracion/dashboard.html')

    def test_gestion_usuarios(self):
        """Test de gestión de usuarios"""
        response = self.client.get(reverse('administracion:gestion_usuarios'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'administracion/gestion_usuarios.html')

    def test_configuracion_sistema(self):
        """Test de configuración del sistema"""
        response = self.client.get(reverse('administracion:configuracion_sistema'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'administracion/configuracion_sistema.html')

class MiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_role_redirect_middleware_paciente(self):
        """Test del middleware de redirección de roles para paciente"""
        paciente = PacienteFactory()
        self.client.login(username=paciente.user.username, password='password123')

        response = self.client.get(reverse('public:landing'))
        self.assertEqual(response.status_code, 302)  # Debe redirigir al dashboard del paciente

    def test_role_redirect_middleware_medico(self):
        """Test del middleware de redirección de roles para médico"""
        medico = MedicoFactory()
        self.client.login(username=medico.user.username, password='password123')

        response = self.client.get(reverse('public:landing'))
        self.assertEqual(response.status_code, 302)  # Debe redirigir al dashboard del médico

    def test_module_access_middleware(self):
        """Test del middleware de acceso a módulos"""
        paciente = PacienteFactory()
        self.client.login(username=paciente.user.username, password='password123')

        # Intentar acceder a una URL de médicos
        response = self.client.get(reverse('medicos:dashboard'))
        self.assertEqual(response.status_code, 403)  # Forbidden