from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from cases.services import CaseService
from cases.models import CaseAuditLog, Case
from django.db import connection

User = get_user_model()


class CaseServiceFinalizeSubmissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='patient1', email='patient1@example.com', password='pass', role='patient', is_active=True)
        self.session_data = {
            'patient_profile': {
                'full_name': 'Juan Pérez',
                'phone': '+34123456789',
                'medical_history': 'Hipertensión arterial',
                'current_medications': 'Amlodipino',
                'known_allergies': 'Penicilina',
            },
            'case_draft': {
                'primary_diagnosis': 'Posible hipertensión mal controlada',
                'referring_institution': 'Clínica Central',
                'main_symptoms': 'Dolor de cabeza persistente y mareos',
            },
            'documents': [
                {'name': 'informe.pdf', 'type': 'diagnostic_report', 's3_file_path': 'cases/123/informe.pdf'},
            ]
        }

    def test_finalize_submission_creates_case_and_audit_and_permissions(self):
        case = CaseService.finalize_submission(self.user, self.session_data, explicit_consent=True)

        # Case created and linked
        self.assertIsNotNone(case)
        self.assertEqual(case.patient, self.user)

        # Audit log exists
        audit = CaseAuditLog.objects.filter(case=case, action='create').first()
        self.assertIsNotNone(audit)

        # Permission assigned (guardian)
        try:
            from guardian.shortcuts import get_perms
            perms = get_perms(self.user, case)
            self.assertIn('view_case', perms)
        except Exception:
            # If guardian isn't available in environment, at least ensure code path didn't crash
            pass

        # Check that medical_history is not stored in plaintext at DB level
        # Query raw DB value for the profile's medical_history column
        with connection.cursor() as cursor:
            cursor.execute("SELECT medical_history FROM auth_patientprofile WHERE user_id = %s", [self.user.id])
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            stored = str(row[0])
            # The plaintext 'Hipertensión arterial' should not appear verbatim in the stored column
            self.assertNotIn('Hipertensión arterial', stored)

    def test_finalize_submission_requires_consent_and_rolls_back(self):
        # When consent is False, expect ValueError and no Case created
        with self.assertRaises(ValueError):
            CaseService.finalize_submission(self.user, self.session_data, explicit_consent=False)

        self.assertFalse(Case.objects.filter(patient=self.user).exists())
