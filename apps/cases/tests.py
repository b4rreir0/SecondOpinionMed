from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Case, CaseAuditLog
from .services import CaseService
from auth.services import PatientRegistrationService, DoctorRegistrationService

CustomUser = get_user_model()


class CaseServiceTest(TestCase):
    """Tests para el servicio de casos"""
    
    def setUp(self):
        """Crea usuarios de prueba"""
        self.patient_user, _ = PatientRegistrationService.register_patient(
            email='patient@test.com',
            password='test1234',
            full_name='Test Patient',
            identity_document='12345',
            phone_number='+34123456789'
        )
        
        self.doctor_user, _ = DoctorRegistrationService.register_doctor(
            email='doctor@test.com',
            password='test1234',
            full_name='Dr. Test',
            medical_license='LIC123',
            specialty='oncology',
            phone_number='+34987654321'
        )
    
    def test_create_case(self):
        """Prueba la creación de un caso"""
        case = CaseService.create_case(
            patient=self.patient_user,
            primary_diagnosis='Diagnóstico de prueba',
            specialty_required='Oncología',
            description='Descripción del caso'
        )
        
        self.assertIsNotNone(case.case_id)
        self.assertEqual(case.patient, self.patient_user)
        self.assertEqual(case.status, 'submitted')
    
    def test_assign_case_to_doctor(self):
        """Prueba la asignación de un caso a un médico"""
        case = CaseService.create_case(
            patient=self.patient_user,
            primary_diagnosis='Diagnóstico',
            specialty_required='Oncología',
            description='Descripción'
        )
        
        CaseService.assign_case_to_doctor(case, self.doctor_user)
        
        case.refresh_from_db()
        self.assertEqual(case.doctor, self.doctor_user)
        self.assertEqual(case.status, 'in_review')
    
    def test_olp_patient_sees_only_own_cases(self):
        """Prueba que un paciente solo ve sus propios casos (OLP)"""
        # Crear segundo paciente
        patient2_user, _ = PatientRegistrationService.register_patient(
            email='patient2@test.com',
            password='test1234',
            full_name='Test Patient 2',
            identity_document='67890',
            phone_number='+34987654321'
        )
        
        # Crear casos para ambos
        case1 = CaseService.create_case(
            patient=self.patient_user,
            primary_diagnosis='Caso 1',
            specialty_required='Oncología',
            description='Caso 1'
        )
        
        case2 = CaseService.create_case(
            patient=patient2_user,
            primary_diagnosis='Caso 2',
            specialty_required='Cardiología',
            description='Caso 2'
        )
        
        # Verificar OLP
        patient1_cases = CaseService.get_patient_cases(self.patient_user)
        self.assertEqual(patient1_cases.count(), 1)
        self.assertEqual(patient1_cases.first(), case1)
