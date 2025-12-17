from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import PatientProfile, DoctorProfile
from .services import PatientRegistrationService, DoctorRegistrationService, AuthenticationService

CustomUser = get_user_model()


class PatientRegistrationServiceTest(TestCase):
    """Tests para el servicio de registro de pacientes"""
    
    def test_register_patient_successfully(self):
        """Prueba el registro exitoso de un paciente"""
        user, patient_profile = PatientRegistrationService.register_patient(
            email='paciente@test.com',
            password='test1234',
            full_name='Juan Pérez',
            identity_document='12345678',
            phone_number='+34912345678'
        )
        
        self.assertEqual(user.email, 'paciente@test.com')
        self.assertEqual(user.role, 'patient')
        self.assertTrue(user.is_patient())
        self.assertEqual(patient_profile.full_name, 'Juan Pérez')
    
    def test_register_doctor_successfully(self):
        """Prueba el registro exitoso de un médico"""
        user, doctor_profile = DoctorRegistrationService.register_doctor(
            email='doctor@test.com',
            password='test1234',
            full_name='Dr. Carlos López',
            medical_license='LIC123456',
            specialty='oncology',
            phone_number='+34987654321'
        )
        
        self.assertEqual(user.email, 'doctor@test.com')
        self.assertEqual(user.role, 'doctor')
        self.assertTrue(user.is_doctor())
        self.assertEqual(doctor_profile.full_name, 'Dr. Carlos López')


class AuthenticationServiceTest(TestCase):
    """Tests para el servicio de autenticación"""
    
    def setUp(self):
        """Crea un usuario para las pruebas"""
        PatientRegistrationService.register_patient(
            email='test@example.com',
            password='test1234',
            full_name='Test User',
            identity_document='12345',
            phone_number='+34123456789'
        )
    
    def test_get_redirect_url_patient(self):
        """Prueba la redirección correcta para pacientes"""
        user = CustomUser.objects.get(email='test@example.com')
        redirect_url = AuthenticationService.get_redirect_url(user)
        self.assertEqual(redirect_url, '/patients/dashboard/')
