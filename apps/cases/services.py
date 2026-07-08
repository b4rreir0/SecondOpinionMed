from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
import uuid

from .models import Case, CaseAuditLog, SecondOpinion

# Estados usados en filtros del flujo activo
PENDING_CASE_STATUSES = [
    'SUBMITTED', 'ASSIGNED', 'PROCESSING', 'MDT_IN_PROGRESS', 'IN_REVIEW',
]
ACTIVE_CASE_STATUSES = PENDING_CASE_STATUSES + [
    'MDT_COMPLETED', 'REPORT_DRAFT', 'REPORT_COMPLETED',
]
COMPLETED_CASE_STATUSES = ['OPINION_COMPLETE', 'CLOSED', 'REPORT_COMPLETED']


def _diagnosis_from_draft(case_draft, tipo_cancer_obj=None):
    """Deriva el texto de diagnóstico desde el borrador o el tipo de cáncer."""
    primary = (case_draft or {}).get('primary_diagnosis')
    if primary:
        return primary
    if tipo_cancer_obj is not None:
        return tipo_cancer_obj.nombre
    nombre = (case_draft or {}).get('tipo_cancer_nombre')
    if nombre:
        return nombre
    tipo_cancer_pk = (case_draft or {}).get('tipo_cancer')
    if tipo_cancer_pk:
        try:
            from medicos.models import TipoCancer
            tc = TipoCancer.objects.filter(pk=tipo_cancer_pk).first()
            if tc:
                return tc.nombre
        except Exception:
            pass
    return ''


def es_lider_del_caso(medico, case):
    """
    Indica si el médico es el líder responsable del caso
    (cierra el caso y envía la respuesta al paciente).
    """
    if not medico or not case:
        return False

    if case.responsable_id and case.responsable_id == medico.pk:
        return True

    if case.medical_group_id:
        lider = case.medical_group.get_lider()
        if lider and lider.pk == medico.pk:
            return True

    localidad = getattr(case, 'localidad', None)
    comite = getattr(localidad, 'comite', None) if localidad else None
    if comite:
        lider_comite = comite.get_lider()
        if lider_comite and lider_comite.pk == medico.pk:
            return True

    return False


def user_can_access_case_document(user, doc):
    """Paciente, médico asignado, líder o miembro del grupo/comité pueden ver documentos."""
    if not user or not user.is_authenticated or not doc:
        return False

    case = doc.case
    if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
        return True
    if case.patient_id == user.id:
        return True
    if case.doctor_id == user.id:
        return True
    if case.responsable_id and getattr(case.responsable, 'usuario_id', None) == user.id:
        return True

    try:
        medico = user.medico
    except Exception:
        return False

    if case.medical_group_id:
        from medicos.models import DoctorGroupMembership
        if DoctorGroupMembership.objects.filter(
            medico=medico, grupo=case.medical_group, activo=True
        ).exists():
            return True

    localidad = getattr(case, 'localidad', None)
    comite = getattr(localidad, 'comite', None) if localidad else None
    if comite and comite.medicos_miembros.filter(pk=medico.pk).exists():
        return True

    return False


def _attach_session_documents(case, user, session_data):
    """
    Vincula al caso los documentos ya subidos en el paso 3
    y elimina registros huérfanos sin archivo.
    """
    from .models import CaseDocument

    documents = session_data.get('documents', []) or []
    linked_ids = []

    for meta in documents:
        doc_id = meta.get('id')
        if not doc_id:
            continue
        doc = CaseDocument.objects.filter(pk=doc_id, case__patient=user).first()
        if not doc:
            doc = CaseDocument.objects.filter(pk=doc_id, uploaded_by=user).first()
        if not doc:
            continue
        if doc.case_id != case.id:
            doc.case = case
            doc.save(update_fields=['case'])
        linked_ids.append(doc.pk)

    ghosts = CaseDocument.objects.filter(case=case).exclude(pk__in=linked_ids)
    for ghost in ghosts:
        if not ghost.has_stored_file:
            ghost.delete()

    return linked_ids


class CaseService:
    """
    Servicio de gestión de casos.
    
    Encapsula la lógica de negocio relacionada con los casos de segunda opinión.
    """
    
    @staticmethod
    @transaction.atomic
    def create_case(patient, primary_diagnosis, specialty_required, description=''):
        """
        Crea un nuevo caso de segunda opinión.
        
        Args:
            patient (CustomUser): Usuario paciente
            primary_diagnosis (str): Diagnóstico primario
            specialty_required (str): Especialidad requerida
            description (str): Reservado (compatibilidad con tests)
            
        Returns:
            Case: Instancia del caso creado
        """
        case_id = f"CASO-{uuid.uuid4().hex[:12].upper()}"
        
        case = Case.objects.create(
            patient=patient,
            case_id=case_id,
            primary_diagnosis=primary_diagnosis,
            specialty_required=specialty_required,
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
        2. Los casos de su grupo médico (MedicalGroup)
        3. Los casos de su comité multidisciplinario (por localidad)
        
        Args:
            doctor: Usuario médico
            include_completed: Si True, incluye casos completados
        """
        from medicos.models import Medico
        
        # DEBUG: Log
        print(f"[get_doctor_assigned_cases] Doctor: {getattr(doctor, 'email', doctor)}")
        print(f"[get_doctor_assigned_cases] Tiene atributo medico: {hasattr(doctor, 'medico')}")
        
        if include_completed:
            statuses = ACTIVE_CASE_STATUSES + COMPLETED_CASE_STATUSES + ['IN_REVIEW', 'COMPLETED']
        else:
            statuses = list(PENDING_CASE_STATUSES)
        
        # Casos donde es el doctor asignado
        qs = Case.objects.filter(
            doctor=doctor,
            status__in=statuses
        )
        print(f"[get_doctor_assigned_cases] Casos propios (doctor={doctor}): {qs.count()}")
        
        # También obtener los casos del grupo médico al que pertenece el médico
        try:
            # Obtener el objeto Medico relacionado con este usuario
            # Primero intentamos con el related_name
            medico = getattr(doctor, 'medico', None)
            
            # Si no tiene el atributo o es None, hacer una consulta directa
            if medico is None:
                try:
                    from medicos.models import Medico
                    medico = Medico.objects.get(usuario=doctor)
                except Medico.DoesNotExist:
                    medico = None
                    print(f"[get_doctor_assigned_cases] No se encontró objeto Medico para el usuario {doctor.email}")
            
            print(f"[get_doctor_assigned_cases] Medico: {medico}")
            
            if medico:
                # Obtener los grupos médicos del médico (vía DoctorGroupMembership)
                from medicos.models import DoctorGroupMembership
                memberships = DoctorGroupMembership.objects.filter(
                    medico=medico,
                    activo=True
                ).select_related('grupo')
                
                if memberships.exists():
                    grupos = [m.grupo for m in memberships]
                    print(f"[get_doctor_assigned_cases] Grupos del medico: {[g.nombre for g in grupos]}")
                    
                    # Casos asignados al grupo médico
                    casos_grupo = Case.objects.filter(
                        medical_group__in=grupos,
                        status__in=statuses
                    )
                    print(f"[get_doctor_assigned_cases] Casos del grupo: {casos_grupo.count()}")
                    qs = qs | casos_grupo
                
                # Obtener los comités del médico (para casos por localidad)
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
                    print(f"[get_doctor_assigned_cases] Casos del comite: {casos_comite.count()}")
                    
                    # Combinar: casos propios + casos del grupo + casos del comité
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
        TipoCancer = django_apps.get_model('medicos', 'TipoCancer')

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

        tipo_cancer_obj = None
        tipo_cancer_pk = case_draft.get('tipo_cancer')
        if tipo_cancer_pk:
            try:
                tipo_cancer_obj = TipoCancer.objects.get(pk=tipo_cancer_pk)
            except (TipoCancer.DoesNotExist, ValueError, TypeError):
                pass

        case_pk = session_data.get('case_pk')
        existing_case = Case.objects.filter(pk=case_pk, patient=user).first() if case_pk else None

        if existing_case:
            case = existing_case
            case.primary_diagnosis = _diagnosis_from_draft(case_draft, tipo_cancer_obj) or case.primary_diagnosis
            case.specialty_required = case_draft.get(
                'especialidad_nombre', case_draft.get('referring_institution', case.specialty_required)
            )
            if case_draft.get('diagnosis_date'):
                case.diagnosis_date = case_draft.get('diagnosis_date')
            case.tipo_cancer = tipo_cancer_obj or case.tipo_cancer
            case.referring_institution = case_draft.get('referring_institution', case.referring_institution)
            case.status = 'SUBMITTED'
            case.save()
        else:
            case_id = f"CASO-{uuid.uuid4().hex[:12].upper()}"
            case = Case.objects.create(
                patient=user,
                case_id=case_id,
                primary_diagnosis=_diagnosis_from_draft(case_draft, tipo_cancer_obj),
                specialty_required=case_draft.get(
                    'especialidad_nombre', case_draft.get('referring_institution', '')
                ),
                diagnosis_date=case_draft.get('diagnosis_date', None) if case_draft.get('diagnosis_date') else None,
                tipo_cancer=tipo_cancer_obj,
                referring_institution=case_draft.get('referring_institution', ''),
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
                    # Asignar al líder del comité si existe, o al médico de la localidad
                    if loc.comite:
                        lider = loc.comite.get_lider()
                        if lider and lider.usuario:
                            try:
                                CaseService.assign_case_to_doctor(case, lider.usuario, responsable=lider)
                            except Exception:
                                pass
                    elif loc.medico and getattr(loc.medico, 'usuario', None):
                        try:
                            CaseService.assign_case_to_doctor(case, loc.medico.usuario)
                        except Exception:
                            pass
        except Exception:
            pass

        # Vincular documentos reales subidos en el paso 3 y limpiar registros vacíos
        _attach_session_documents(case, user, session_data)

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
    def assign_case_to_doctor(case, doctor, responsable=None):
        """
        Asigna un caso a un médico.
        
        Args:
            case (Case): El caso a asignar
            doctor (CustomUser): El médico asignado
            responsable (Medico): Líder responsable del caso (opcional)
        """
        case.doctor = doctor
        if responsable is not None:
            case.responsable = responsable
        elif case.medical_group_id:
            lider = case.medical_group.get_lider()
            if lider:
                case.responsable = lider
        case.status = 'IN_REVIEW'
        # Solo actualizar assigned_at si no ha sido establecido antes
        if not case.assigned_at:
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
    2. Asigna al líder del grupo como responsable del caso
    3. Asigna el caso al grupo y responsable
    4. Envía notificaciones a los miembros del grupo
    
    Args:
        case (Case): El caso a asignar
        
    Returns:
        tuple: (success: bool, message: str)
    """
    from medicos.models import MedicalGroup, DoctorGroupMembership, Medico
    
    with transaction.atomic():
        # Buscar grupo por tipo_cancer del caso (ahora es FK directa)
        if case.tipo_cancer and case.tipo_cancer.grupo_medico:
            grupo = case.tipo_cancer.grupo_medico
            if not grupo.activo:
                grupo = None
        else:
            grupo = None
        
        # Fallback: buscar por specialty_required si no se encontró por tipo_cancer
        if not grupo:
            try:
                grupo = MedicalGroup.objects.get(
                    nombre__icontains=case.specialty_required,
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
                return (False, f"No se encontró grupo médico para: {case.specialty_required}")
        
        responsable = _seleccionar_responsable(grupo)
        
        if not responsable:
            return (False, f"No hay médicos disponibles en el grupo: {grupo.nombre}")
        
        case.medical_group = grupo
        case.responsable = responsable
        case.doctor = responsable.usuario
        # Solo actualizar assigned_at si no ha sido establecido antes
        if not case.assigned_at:
            case.assigned_at = timezone.now()
        case.save()
        
        _notificar_asignacion_caso(case, grupo)
        
        return (True, f"Caso asignado al grupo {grupo.nombre} y responsable {responsable.nombre_completo}")


def _seleccionar_responsable(grupo):
    """El responsable del caso es siempre el líder del grupo MDT."""
    return grupo.get_lider()


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
            enlace=f'/doctors/case/{case.case_id}/',
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
