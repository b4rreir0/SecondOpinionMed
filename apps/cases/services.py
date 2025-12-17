from django.db import transaction
from .models import Case


def create_case(patient, case_id, primary_diagnosis, specialty_required, description):
    """Crea un `Case` dentro de una transacción y devuelve la instancia."""
    with transaction.atomic():
        case = Case.objects.create(
            patient=patient,
            case_id=case_id,
            primary_diagnosis=primary_diagnosis,
            specialty_required=specialty_required,
            description=description,
        )
        return case
    
    @staticmethod
    @transaction.atomic
    def finalize_submission(user, session_data, explicit_consent: bool = False):
        """
        Crea/actualiza PatientProfile y crea un Case a partir de los datos recogidos en la sesión.

        Args:
            user: CustomUser paciente
            session_data: dict con keys 'patient_profile', 'case_draft', 'documents'
            explicit_consent: bool, debe ser True para proceder

        Returns:
            Case: instancia creada
        """
        if not explicit_consent:
            raise ValueError('Consentimiento explícito requerido para enviar la solicitud')

        patient_profile_data = session_data.get('patient_profile', {})
        case_draft = session_data.get('case_draft', {})
        documents = session_data.get('documents', [])

        # Import models lazily to avoid app registry issues
        from django.apps import apps as django_apps
        PatientProfile = django_apps.get_model('authentication', 'PatientProfile')
        CaseDocument = django_apps.get_model('cases', 'CaseDocument')

        # Create or update patient profile
        profile, created = PatientProfile.objects.get_or_create(user=user)
        if patient_profile_data:
            if patient_profile_data.get('full_name'):
                profile.full_name = patient_profile_data.get('full_name')
            if patient_profile_data.get('phone'):
                profile.phone_number = patient_profile_data.get('phone')
            if patient_profile_data.get('medical_history'):
                profile.medical_history = patient_profile_data.get('medical_history')
            if patient_profile_data.get('current_medications'):
                profile.current_treatment = patient_profile_data.get('current_medications')
            if patient_profile_data.get('known_allergies'):
                profile.medical_history = (profile.medical_history or '') + '\n\nAlergias:\n' + patient_profile_data.get('known_allergies')
            profile.save()

        # Create Case (start as DRAFT then submit via FSM)
        case_id = f"CASO-{uuid.uuid4().hex[:12].upper()}"
        case = Case.objects.create(
            patient=user,
            case_id=case_id,
            primary_diagnosis=case_draft.get('primary_diagnosis', '') if case_draft else '',
            specialty_required=case_draft.get('referring_institution', '') if case_draft else '',
            description=case_draft.get('main_symptoms', '') if case_draft else '',
        )

        # Link documents: create CaseDocument rows if session contains metadata
        for d in documents:
            try:
                CaseDocument.objects.create(
                    case=case,
                    document_type=d.get('type', 'other'),
                    file_name=d.get('name', ''),
                    uploaded_by=user,
                    s3_file_path=d.get('s3_key', d.get('s3_file_path', ''))
                )
            except Exception:
                continue

        # Transition FSM to SUBMITTED (or fallback)
        try:
            case.submit_case()
            case.save()
        except Exception:
            case.status = 'SUBMITTED'
            case.save()

        # Audit
        CaseAuditLog.objects.create(
            case=case,
            user=user,
            action='create',
            description='Caso enviado desde flujo SOP'
        )

        # Assign object permissions to patient
        try:
            from guardian.shortcuts import assign_perm
            assign_perm('view_case', user, case)
            assign_perm('change_case', user, case)
        except Exception:
            pass

        return case


def submit_case_service(case: Case):
    """Validaciones finales y transición a SUBMITTED."""
    # Aquí se pueden agregar validaciones adicionales de negocio
    case.submit_case()
    case.save()
    return case
from django.db import transaction
from django.utils import timezone
import uuid

from .models import Case, CaseAuditLog, SecondOpinion


class CaseService:
    """
    Servicio de gestión de casos.
    
    Encapsula la lógica de negocio relacionada con los casos de segunda opinión.
    """
    
    @staticmethod
    @transaction.atomic
    def create_case(patient, primary_diagnosis, specialty_required, description):
        """
        Crea un nuevo caso de segunda opinión.
        
        Args:
            patient (CustomUser): Usuario paciente
            primary_diagnosis (str): Diagnóstico primario
            specialty_required (str): Especialidad requerida
            description (str): Descripción del caso
            
        Returns:
            Case: Instancia del caso creado
        """
        case_id = f"CASO-{uuid.uuid4().hex[:12].upper()}"
        
        case = Case.objects.create(
            patient=patient,
            case_id=case_id,
            primary_diagnosis=primary_diagnosis,
            specialty_required=specialty_required,
            description=description,
            status='SUBMITTED'
        )
        
        # Registrar en auditoría
        CaseAuditLog.objects.create(
            case=case,
            user=patient,
            action='create',
            description='Caso creado por el paciente'
        )

        # Asignar permisos a nivel de objeto (Principio del Mínimo Necesario)
        try:
            from guardian.shortcuts import assign_perm
            assign_perm('view_case', patient, case)
            assign_perm('change_case', patient, case)
        except Exception:
            # guardian no disponible en entornos ligeros; continuar sin fallo
            pass
        
        return case
    
    @staticmethod
    def get_patient_cases(patient):
        """
        Obtiene todos los casos de un paciente.
        
        Implementa Permisos a Nivel de Objeto (OLP).
        """
        return Case.objects.filter(patient=patient)
    
    @staticmethod
    def get_doctor_assigned_cases(doctor):
        """
        Obtiene todos los casos asignados a un médico.
        
        Implementa Permisos a Nivel de Objeto (OLP).
        """
        return Case.objects.filter(
            doctor=doctor,
            status__in=['paid', 'in_review', 'clarification_needed']
        )

    @staticmethod
    @transaction.atomic
    def finalize_submission(user, session_data, explicit_consent: bool = False):
        """
        Crea/actualiza PatientProfile y crea un Case a partir de los datos recogidos en la sesión.

        Args:
            user: CustomUser paciente
            session_data: dict con keys 'patient_profile', 'case_draft', 'documents'
            explicit_consent: bool, debe ser True para proceder

        Returns:
            Case: instancia creada
        """
        if not explicit_consent:
            raise ValueError('Consentimiento explícito requerido para enviar la solicitud')

        patient_profile_data = session_data.get('patient_profile', {}) or {}
        case_draft = session_data.get('case_draft', {}) or {}
        documents = session_data.get('documents', []) or []

        # Import models lazily to avoid app registry issues
        from django.apps import apps as django_apps
        PatientProfile = django_apps.get_model('authentication', 'PatientProfile')
        CaseDocument = django_apps.get_model('cases', 'CaseDocument')

        # Create or update patient profile
        profile, created = PatientProfile.objects.get_or_create(user=user)
        if patient_profile_data:
            if patient_profile_data.get('full_name'):
                profile.full_name = patient_profile_data.get('full_name')
            if patient_profile_data.get('phone'):
                profile.phone_number = patient_profile_data.get('phone')
            if patient_profile_data.get('medical_history'):
                profile.medical_history = patient_profile_data.get('medical_history')
            if patient_profile_data.get('current_medications'):
                profile.current_treatment = patient_profile_data.get('current_medications')
            if patient_profile_data.get('known_allergies'):
                # append allergies to medical_history to avoid schema mismatches
                profile.medical_history = (profile.medical_history or '') + '\n\nAlergias:\n' + patient_profile_data.get('known_allergies')
            profile.save()

        # Create Case
        case_id = f"CASO-{uuid.uuid4().hex[:12].upper()}"
        case = Case.objects.create(
            patient=user,
            case_id=case_id,
            primary_diagnosis=case_draft.get('primary_diagnosis', ''),
            specialty_required=case_draft.get('referring_institution', ''),
            description=case_draft.get('main_symptoms', ''),
            status='SUBMITTED'
        )

        # Link documents: create CaseDocument rows if session contains metadata
        for d in documents:
            try:
                CaseDocument.objects.create(
                    case=case,
                    document_type=d.get('type', 'other'),
                    file_name=d.get('name', ''),
                    uploaded_by=user,
                    s3_file_path=d.get('s3_key', d.get('s3_file_path', ''))
                )
            except Exception:
                continue

        # Audit
        try:
            CaseAuditLog.objects.create(
                case=case,
                user=user,
                action='create',
                description='Caso enviado desde flujo SOP'
            )
        except Exception:
            pass

        # Assign object permissions to patient
        try:
            from guardian.shortcuts import assign_perm
            assign_perm('view_case', user, case)
            assign_perm('change_case', user, case)
        except Exception:
            pass

        return case
    
    @staticmethod
    @transaction.atomic
    def assign_case_to_doctor(case, doctor):
        """
        Asigna un caso a un médico.
        
        Args:
            case (Case): El caso a asignar
            doctor (CustomUser): El médico asignado
        """
        case.doctor = doctor
        case.status = 'IN_REVIEW'
        case.assigned_at = timezone.now()
        case.save()
        
        # Registrar en auditoría
        CaseAuditLog.objects.create(
            case=case,
            user=doctor,
            action='update',
            description=f'Caso asignado al médico {doctor.email}'
        )
        # Asignar permisos al médico
        try:
            from guardian.shortcuts import assign_perm
            assign_perm('view_case', doctor, case)
            assign_perm('change_case', doctor, case)
        except Exception:
            pass
    
    @staticmethod
    @transaction.atomic
    def request_clarification(case, doctor, reason):
        """
        El médico solicita aclaración al paciente.
        
        Args:
            case (Case): El caso
            doctor (CustomUser): El médico
            reason (str): Razón de la aclaración requerida
        """
        case.status = 'CLARIFICATION_NEEDED'
        case.save()
        
        # Registrar en auditoría
        CaseAuditLog.objects.create(
            case=case,
            user=doctor,
            action='clarification_requested',
            description=f'Aclaración solicitada: {reason}'
        )
    
    @staticmethod
    @transaction.atomic
    def complete_case(case, doctor, opinion_text, recommendations=''):
        """
        Finaliza un caso con la opinión del médico.
        
        Args:
            case (Case): El caso
            doctor (CustomUser): El médico
            opinion_text (str): Texto de la opinión
            recommendations (str): Recomendaciones (opcional)
        """
        case.status = 'OPINION_COMPLETE'
        case.completed_at = timezone.now()
        case.save()
        
        # Crear la opinión
        SecondOpinion.objects.create(
            case=case,
            doctor=doctor,
            opinion_text=opinion_text,
            recommendations=recommendations
        )
        
        # Registrar en auditoría
        CaseAuditLog.objects.create(
            case=case,
            user=doctor,
            action='opinion_added',
            description='Opinión médica completada'
        )
        # Optionally schedule deletion of case files after opinion complete
        try:
            from django.conf import settings
            if getattr(settings, 'AUTO_DELETE_CASE_FILES', False):
                # Use documents service to schedule deletion
                try:
                    from documents.services import schedule_delete_case_files
                    schedule_delete_case_files(case.case_id, delay_seconds=getattr(settings, 'AUTO_DELETE_DELAY_SECONDS', 0))
                except Exception:
                    # Log but don't fail the operation
                    import logging
                    logging.getLogger(__name__).exception('Failed to schedule case file deletion for case %s', case.case_id)
        except Exception:
            pass
    
    @staticmethod
    def log_case_access(case, user, action='read'):
        """
        Registra el acceso a un caso en la auditoría.
        
        Args:
            case (Case): El caso
            user (CustomUser): El usuario que accede
            action (str): Tipo de acción
        """
        CaseAuditLog.objects.create(
            case=case,
            user=user,
            action=action
        )
