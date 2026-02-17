from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
import uuid

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
    def get_doctor_assigned_cases(doctor, include_completed=False):
        """
        Obtiene todos los casos asignados a un médico.
        
        Implementa Permisos a Nivel de Objeto (OLP).
        Un médico puede ver:
        1. Los casos donde es el doctor asignado directamente
        2. Los casos de su comité multidisciplinario
        
        Args:
            doctor: Usuario médico
            include_completed: Si True, incluye casos completados
        """
        from medicos.models import Medico
        
        # DEBUG: Log
        print(f"[get_doctor_assigned_cases] Doctor: {getattr(doctor, 'email', doctor)}")
        print(f"[get_doctor_assigned_cases] Tiene atributo medico: {hasattr(doctor, 'medico')}")
        
        # Determinar estados a incluir
        if include_completed:
            statuses = ['PAID', 'IN_REVIEW', 'CLARIFICATION_NEEDED', 'ASSIGNED', 'PROCESSING', 'COMPLETED']
        else:
            statuses = ['PAID', 'IN_REVIEW', 'CLARIFICATION_NEEDED', 'ASSIGNED', 'PROCESSING']
        
        # Casos donde es el doctor asignado
        qs = Case.objects.filter(
            doctor=doctor,
            status__in=statuses
        )
        print(f"[get_doctor_assigned_cases] Casos propios (sin filtro estado): {Case.objects.filter(doctor=doctor).count()}")
        
        # También obtener los casos del comité al que pertenece el médico
        try:
            # Obtener el objeto Medico relacionado con este usuario
            medico = getattr(doctor, 'medico', None)
            print(f"[get_doctor_assigned_cases] Medico: {medico}")
            
            if medico:
                # Obtener los comités del médico
                comites = medico.comites.all()
                print(f"[get_doctor_assigned_cases] Comites del medico: {comites.count()}")
                
                if comites.exists():
                    # Obtener las localidades de esos comités
                    from medicos.models import Localidad
                    localidades = Localidad.objects.filter(comite__in=comites)
                    print(f"[get_doctor_assigned_cases] Localidades: {localidades.count()}")
                    
                    # Obtener casos de esas localidades
                    casos_comite = Case.objects.filter(
                        localidad__in=localidades,
                        status__in=statuses
                    )
                    print(f"[get_doctor_assigned_cases] Casos del comite (sin filtro estado): {casos_comite.count()}")
                    
                    # Combinar: casos propios + casos del comité
                    qs = qs | casos_comite
        except Exception as e:
            # Si hay algún error, simplemente devolver los casos propios
            print(f"Error getting committee cases: {e}")
        
        try:
            print(f"[CaseService] Doctor {getattr(doctor, 'email', doctor)} assigned cases count: {qs.count()}")
        except Exception:
            pass
        return qs.distinct()

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
            diagnosis_date=case_draft.get('diagnosis_date', None) if case_draft.get('diagnosis_date') else None,
            status='SUBMITTED'
        )

        # If a localidad id was provided in the draft, try to assign the corresponding Medico
        try:
            localidad_id = case_draft.get('localidad')
            if localidad_id:
                from medicos.models import Localidad
                loc = Localidad.objects.filter(pk=localidad_id).first()
                # persist localidad on case for later visibility
                if loc:
                    try:
                        case.localidad = loc
                        case.save()
                    except Exception:
                        pass
                
                # Asignar al líder del comité si existe, o al médico de la localidad
                if loc:
                    # Primero verificar si hay un comité asignado a la localidad
                    if loc.comite and loc.comite.medicos_miembros.exists():
                        # Asignar al primer miembro del comité (el líder)
                        primer_medico = loc.comite.medicos_miembros.first()
                        if primer_medico and primer_medico.usuario:
                            try:
                                CaseService.assign_case_to_doctor(case, primer_medico.usuario)
                            except Exception:
                                pass
                    # Si no hay comité, usar el médico de la localidad
                    elif loc.medico and getattr(loc.medico, 'usuario', None):
                        try:
                            CaseService.assign_case_to_doctor(case, loc.medico.usuario)
                        except Exception:
                            pass
        except Exception:
            pass

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
        try:
            print(f"[CaseService] Case {case.case_id} assigned to doctor {getattr(doctor, 'email', doctor)} and set to IN_REVIEW")
        except Exception:
            pass
        
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


# =============================================================================
# SERVICIOS DE ASIGNACIÓN (Nuevo Sistema MDT)
# =============================================================================

def asignar_caso_automatico(case):
    """
    Asigna automáticamente un caso al grupo médico correspondiente y a un responsable.
    
    Este servicio:
    1. Determina el MedicalGroup según el tipo_cancer del caso
    2. Selecciona un responsable (round-robin o por defecto)
    3. Asigna el caso al grupo y responsable
    4. Envía notificaciones a los miembros del grupo
    
    Args:
        case (Case): El caso a asignar
        
    Returns:
        tuple: (success: bool, message: str)
    """
    from medicos.models import MedicalGroup, DoctorGroupMembership, Medico
    
    with transaction.atomic():
        try:
            grupo = MedicalGroup.objects.get(
                tipo_cancer__codigo__iexact=case.specialty_required,
                activo=True
            )
        except MedicalGroup.DoesNotExist:
            try:
                grupo = MedicalGroup.objects.filter(
                    nombre__icontains=case.specialty_required,
                    activo=True
                ).first()
            except Exception:
                pass
            
            if not grupo:
                return (False, f"No se encontró grupo médico para la especialidad: {case.specialty_required}")
        
        responsable = _seleccionar_responsable(grupo)
        
        if not responsable:
            return (False, f"No hay médicos disponibles en el grupo: {grupo.nombre}")
        
        case.medical_group = grupo
        case.responsable = responsable
        case.doctor = responsable.usuario
        case.assigned_at = timezone.now()
        case.save()
        
        _notificar_asignacion_caso(case, grupo)
        
        return (True, f"Caso asignado al grupo {grupo.nombre} y responsable {responsable.nombre_completo}")


def _seleccionar_responsable(grupo):
    """Selecciona el médico responsable usando algoritmo round-robin."""
    from medicos.models import Medico
    from django.db.models import Count, Q
    
    if grupo.responsable_por_defecto:
        if (grupo.responsable_por_defecto.estado == 'activo' and 
            grupo.responsable_por_defecto.disponible_segundas_opiniones):
            return grupo.responsable_por_defecto
    
    miembros = grupo.miembros.filter(
        estado='activo',
        disponible_segundas_opiniones=True
    ).annotate(
        casos_activos=Count(
            'usuario__doctor_cases',
            filter=Q(usuario__doctor_cases__status__in=['PROCESSING', 'IN_REVIEW'])
        )
    ).order_by('casos_activos', 'fecha_ingreso')
    
    return miembros.first()


def _notificar_asignacion_caso(case, grupo):
    """Envía notificaciones a todos los miembros del grupo médico."""
    from notifications.models import Notification
    
    titulo = f"Nuevo caso asignado: {case.case_id}"
    mensaje = f"Se ha asignado un nuevo caso de {case.specialty_required} al grupo {grupo.nombre}."
    
    for membresia in grupo.miembros.filter(activo=True):
        medico = membresia.medico
        Notification.objects.create(
            receptor=medico.usuario,
            tipo='asignacion_caso',
            titulo=titulo,
            mensaje=mensaje,
            enlace=f'/medicos/casos/{case.id}/',
            caso_id=case.case_id
        )


def obtener_estadisticas_grupo(grupo):
    """Obtiene estadísticas de un grupo médico."""
    return {
        'numero_miembros': grupo.miembros.filter(activo=True).count(),
        'miembros_activos': grupo.numero_miembros,
        'quorum_config': grupo.quorum_config,
        'puede_asignar': grupo.puede_asignar_caso(),
    }


def verificar_quorum(case):
    """Verifica si se ha alcanzado el quorum de opiniones para un caso."""
    if not hasattr(case, 'medical_group'):
        return {'alcanzado': False, 'mensaje': 'Sin grupo asignado', 'votos_totales': 0}
    
    votos_totales = case.opiniones.count()
    quorum_requerido = case.medical_group.quorum_config
    
    return {
        'alcanzado': votos_totales >= quorum_requerido,
        'votos_totales': votos_totales,
        'quorum_requerido': quorum_requerido,
        'faltantes': max(0, quorum_requerido - votos_totales)
    }
