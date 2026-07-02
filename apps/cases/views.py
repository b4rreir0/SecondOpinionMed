from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseRedirect, FileResponse
from django.urls import reverse
from django.utils import timezone

from .models import Case
from .mdt_models import MDTMessage
from .services import CaseService, PENDING_CASE_STATUSES, COMPLETED_CASE_STATUSES


class PatientDashboardView(LoginRequiredMixin, View):
    """
    Dashboard del Paciente.
    
    Muestra los casos del paciente y permite crear nuevos casos.
    Implementa Permisos a Nivel de Objeto (OLP) para que solo vea sus datos.
    """
    template_name = 'patients/dashboard.html'
    login_url = 'auth:login'
    
    def get(self, request):
        """Muestra el dashboard del paciente"""
        if not request.user.is_patient():
            return redirect('/')
        
        # OLP: Solo obtener casos del paciente actual
        cases = CaseService.get_patient_cases(request.user)
        # Obtener el último caso (por created_at) para mostrar resumen rápido
        latest_case = cases.first() if cases.exists() else None

        context = {
            'cases': cases,
            'latest_case': latest_case,
            'user_role': 'patient'
        }
        return render(request, self.template_name, context)


class PatientCaseDetailView(LoginRequiredMixin, View):
    """
    Detalle de un caso del Paciente.
    
    Muestra los detalles del caso y sus documentos.
    OLP: Verifica que el usuario sea el propietario del caso.
    """
    template_name = 'patients/case_detail.html'
    login_url = 'auth:login'
    
    def get(self, request, case_id):
        """Muestra detalle del caso"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[PatientCaseDetailView] Iniciando carga para case_id={case_id}")
        logger.info(f"[PatientCaseDetailView] Usuario autenticado: {request.user.is_authenticated}")
        logger.info(f"[PatientCaseDetailView] Usuario: {request.user.email if request.user.is_authenticated else 'No autenticado'}")
        
        # Verificar que el usuario está autenticado
        if not request.user.is_authenticated:
            logger.warning("[PatientCaseDetailView] Usuario no autenticado, redireccionando")
            return redirect(self.login_url)
        
        # Verificar que es un paciente
        if not request.user.is_patient():
            logger.warning(f"[PatientCaseDetailView] Usuario {request.user.email} no es paciente, raising 404")
            raise Http404()
        
        logger.info(f"[PatientCaseDetailView] Usuario es paciente: {request.user.is_patient()}")
        
        # Obtener el caso
        try:
            case = get_object_or_404(Case, case_id=case_id)
            logger.info(f"[PatientCaseDetailView] Caso encontrado: {case.case_id}, patient={case.patient.email}")
        except Http404:
            raise
        except Exception as e:
            logger.error(f"[PatientCaseDetailView] Error al obtener caso {case_id}: {e}")
            raise Http404("Caso no encontrado")
        
        # OLP: Verificar que el usuario es el paciente del caso
        logger.info(f"[PatientCaseDetailView] Verificando permisos: request.user={request.user.email} vs case.patient={case.patient.email}")
        if case.patient != request.user:
            logger.warning(f"[PatientCaseDetailView] Usuario {request.user.email} no es el paciente del caso {case.case_id}")
            raise Http404("No tienes permiso para ver este caso.")
        
        logger.info(f"[PatientCaseDetailView] Permisos verificados correctamente")
        
        # Registrar acceso
        try:
            CaseService.log_case_access(case, request.user, 'read')
            logger.info(f"[PatientCaseDetailView] Acceso registrado")
        except Exception as e:
            logger.warning(f"[PatientCaseDetailView] Error al registrar acceso: {e}")

        # Obtener la segunda opinión de forma segura
        try:
            opinion = getattr(case, 'second_opinion', None)
            logger.info(f"[PatientCaseDetailView] Opinion: {opinion}")
        except Exception as e:
            logger.warning(f"[PatientCaseDetailView] Error al obtener second_opinion: {e}")
            opinion = None
        
        # Obtener documentos de forma segura
        try:
            documents = case.documents.all()
            logger.info(f"[PatientCaseDetailView] Documentos encontrados: {documents.count()}")
        except Exception as e:
            logger.warning(f"[PatientCaseDetailView] Error al obtener documentos: {e}")
            documents = []
        
        logger.info(f"[PatientCaseDetailView] Renderizando plantilla con context: case={case.case_id}, documents_count={len(documents)}, opinion={opinion is not None}")
        
        # Mostrar todos los campos del caso para debug
        logger.info(f"[PatientCaseDetailView] case.primary_diagnosis = {case.primary_diagnosis}")
        logger.info(f"[PatientCaseDetailView] case.status = {case.status}")
        logger.info(f"[PatientCaseDetailView] case.patient = {case.patient.email}")
        
        # Obtener el informe final
        from .models import FinalReport
        import os
        from django.conf import settings
        
        informe_final = None
        
        # Buscar en la base de datos
        logger.info(f"[PatientCaseDetailView] Buscando FinalReport...")
        informe_final = FinalReport.objects.filter(case=case).first()
        if not informe_final:
            # Usar case__case_id para buscar por el campo case_id del modelo Case
            informe_final = FinalReport.objects.filter(case__case_id=case.case_id).first()
        
        logger.info(f"[PatientCaseDetailView] FinalReport encontrado: {informe_final}")
        
        # Si no existe, buscar el archivo PDF directamente
        if not informe_final:
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'cases', 'reports')
            pdf_filename = f'respuesta_{case.case_id}.pdf'
            pdf_final_url = None
            
            logger.info(f"[PatientCaseDetailView] Buscando PDF en: {reports_dir}")
            
            if os.path.exists(reports_dir):
                for root, dirs, files in os.walk(reports_dir):
                    if pdf_filename in files:
                        rel_path = os.path.relpath(os.path.join(root, pdf_filename), settings.MEDIA_ROOT)
                        pdf_final_url = f'/media/{rel_path.replace(os.sep, "/")}'
                        logger.info(f"[PatientCaseDetailView] PDF encontrado: {pdf_final_url}")
                        break
            
            if pdf_final_url:
                class TempInformeFinal:
                    def __init__(self, url, fecha):
                        self.pdf_file_url = url
                        self.fecha_emision = fecha
                    @property
                    def pdf_file(self):
                        class TempFile:
                            def __init__(self, url):
                                self.url = url
                        return TempFile(self.pdf_file_url)
                
                logger.info(f"[PatientCaseDetailView] Creando TempInformeFinal...")
                informe_final = TempInformeFinal(pdf_final_url, case.updated_at)
        
        logger.info(f"[PatientCaseDetailView] informe_final final: {informe_final}")
        
        context = {
            'case': case,
            'documents': documents,
            'opinion': opinion,
            'informe_final': informe_final
        }
        return render(request, self.template_name, context)


class DoctorDashboardView(LoginRequiredMixin, View):
    """
    Dashboard del Médico.
    
    Muestra los casos asignados al médico.
    Implementa RBAC y OLP para que solo vea sus casos asignados.
    """
    template_name = 'doctors/dashboard_modern.html'
    login_url = 'auth:login'
    
    def get(self, request):
        """Muestra el dashboard del médico"""
        if not request.user.is_doctor():
            return redirect('/')
        
        # Verificar que el usuario tenga un perfil de doctor usando hasattr
        # para evitar problemas de importación circular
        if not hasattr(request.user, 'doctor_profile') or request.user.doctor_profile is None:
            # Si no tiene perfil de doctor, mostrar mensaje de error y redirigir al inicio
            from django.contrib import messages
            messages.error(request, 'Debe completar su perfil de médico para acceder al dashboard.')
            return redirect('home')
        
        doctor_profile = request.user.doctor_profile
        
        # OLP: Solo obtener casos asignados al médico
        assigned_cases = CaseService.get_doctor_assigned_cases(request.user)
        
        # Casos pendientes (con filtros de estado)
        pending_cases = assigned_cases.filter(
            status__in=PENDING_CASE_STATUSES
        )
        
        context = {
            'cases': assigned_cases,
            'casos_pendientes': pending_cases,
            'casos_pendientes_count': pending_cases.count(),
            'user_role': 'doctor',
            'doctor_profile': doctor_profile
        }
        return render(request, self.template_name, context)


class DoctorCaseDetailView(LoginRequiredMixin, View):
    """
    Detalle de un caso para el Médico.
    
    Muestra todos los detalles y documentos del caso.
    OLP: Verifica que el usuario sea el médico asignado.
    """
    template_name = 'doctors/case_detail_modern.html'
    login_url = 'auth:login'
    
    def get(self, request, case_id):
        """Muestra detalle del caso"""
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        
        # OLP: Verificar que el usuario es el médico asignado O pertenece al comité del caso
        puede_ver = False
        
        # 1. Si es el doctor asignado
        if case.doctor == request.user:
            puede_ver = True
        
        # 2. Si pertenece al grupo médico del caso (vía DoctorGroupMembership)
        if not puede_ver and case.medical_group:
            try:
                from medicos.models import Medico, DoctorGroupMembership
                medico = Medico.objects.get(usuario=request.user)
                # Verificar membresía activa en el grupo
                membresia = DoctorGroupMembership.objects.filter(
                    medico=medico,
                    grupo=case.medical_group,
                    activo=True
                ).exists()
                if membresia:
                    puede_ver = True
            except Exception:
                pass
        
        # 3. Si es miembro del comité de la localidad del caso
        if not puede_ver and case.localidad:
            try:
                from medicos.models import Medico
                medico = Medico.objects.get(usuario=request.user)
                comites = medico.comites.all()
                if comites.exists() and case.localidad.comite in comites:
                    puede_ver = True
            except Exception:
                pass
        
        if not puede_ver:
            raise Http404("No tienes permiso para ver este caso.")
        
        # Registrar acceso
        CaseService.log_case_access(case, request.user, 'read')
        
        # Si el caso está en SUBMITTED, ASSIGNED o PROCESSING y el usuario pertenece al grupo,
        # cambiar el estado a IN_REVIEW
        if case.status in ['SUBMITTED', 'ASSIGNED', 'PROCESSING'] and puede_ver:
            case.status = 'IN_REVIEW'
            # Solo actualizar assigned_at si no ha sido establecido antes
            if not case.assigned_at:
                case.assigned_at = timezone.now()
            case.save()
            print(f"[DoctorCaseDetailView] Case {case.case_id} status changed to IN_REVIEW")
        
        # Obtener antecedentes médicos del paciente
        try:
            from pacientes.models import AntecedenteMedico
            antecedentes = case.patient.antecedentes.filter(activo=True)
            antecedentes_personales = antecedentes.filter(tipo='personal')
            antecedentes_familiares = antecedentes.filter(tipo='familiar')
            antecedentes_quirurgicos = antecedentes.filter(tipo='quirurgico')
            alergias = antecedentes.filter(tipo='alergia')
            medicamentos = antecedentes.filter(tipo='medicamento')
        except Exception:
            antecedentes_personales = []
            antecedentes_familiares = []
            antecedentes_quirurgicos = []
            alergias = []
            medicamentos = []
        
        # Calcular edad del paciente (a traves de patient_profile)
        patient_edad = None
        patient_nombre = None
        paciente = None
        try:
            paciente = case.patient.patient_profile
            if paciente:
                # Nombre del paciente
                patient_nombre = paciente.full_name
                
                # Calcular edad
                if paciente.date_of_birth:
                    from datetime import date
                    today = date.today()
                    patient_edad = today.year - paciente.date_of_birth.year - ((today.month, today.day) < (paciente.date_of_birth.month, paciente.date_of_birth.day))
        except Exception as e:
            print(f"Error getting patient profile: {e}")
            patient_edad = None
        
        # Obtener genero del paciente
        try:
            if paciente and hasattr(paciente, 'genero'):
                genero = paciente.get_genero_display() if paciente.genero else 'No especificado'
                patient_genero = genero
            else:
                patient_genero = 'No especificado'
        except Exception as e:
            print(f"Error getting patient gender: {e}")
            patient_genero = 'No especificado'
            patient_genero = 'No especificado'
        
        # Obtener opiniones de los miembros del comité
        from .models import MedicalOpinion
        opiniones = MedicalOpinion.objects.filter(case=case)
        
        # Obtener la opinión del médico actual (si existe)
        try:
            from medicos.models import Medico
            medico_actual = Medico.objects.get(usuario=request.user)
            opinion_medico_actual = MedicalOpinion.objects.filter(case=case, doctor=medico_actual).first()
            
            # Verificar si es el responsable del caso
            es_responsable = False
            
            # 1. Si es el doctor asignado
            if case.doctor == request.user:
                es_responsable = True
            
            # 2. Si es responsable del grupo médico del caso
            if not es_responsable and case.medical_group:
                if hasattr(medico_actual, 'doctorgroupmembership_set'):
                    memberships = medico_actual.doctorgroupmembership_set.filter(grupo=case.medical_group)
                    es_responsable = any(m.es_responsable for m in memberships)
            
            # 3. Si es el coordinador del comité de la localidad
            if not es_responsable and case.localidad and case.localidad.comite:
                comite = case.localidad.comite
                # Verificar si es miembro del comité Y coordinador
                if hasattr(medico_actual, 'comites'):
                    comites_medico = medico_actual.comites.all()
                    if comite in comites_medico:
                        # Es miembro - ahora verificar si es coordinador
                        if comite.coordinador == medico_actual:
                            es_responsable = True
            
            # 4. Si es el coordinador del grupo médico (responsable_por_defecto)
            if not es_responsable and case.medical_group:
                if case.medical_group.responsable_por_defecto == medico_actual:
                    es_responsable = True
        except Exception:
            opinion_medico_actual = None
            es_responsable = False
        
        # Determinar si el caso está completado
        # Estados considerados como completados: MDT_COMPLETED, REPORT_DRAFT, REPORT_COMPLETED, OPINION_COMPLETE, CLOSED
        estados_completados = ['MDT_COMPLETED', 'REPORT_DRAFT', 'REPORT_COMPLETED', 'OPINION_COMPLETE', 'CLOSED']
        caso_completado = case.status in estados_completados
        
        # Determinar si el usuario puede cerrar el caso
        # Solo puede cerrar si:
        # 1. Es responsable/coordinador
        # 2. El caso está en un estado que permite cierre (IN_REVIEW, PROCESSING, MDT_IN_PROGRESS)
        puede_cerrar_caso = False
        estados_permitidos = ['IN_REVIEW', 'PROCESSING', 'MDT_IN_PROGRESS']
        if es_responsable and case.status in estados_permitidos:
            puede_cerrar_caso = True
        
        # Obtener el informe final si existe
        from .models import FinalReport
        informe_final = FinalReport.objects.filter(case=case).first()
        
        context = {
            'caso': case,  # Usar 'caso' para compatibilidad con el template
            'case': case,  # También mantener 'case'
            'patient_profile': case.patient.patient_profile,
            'patient_nombre': patient_nombre,
            'patient_edad': patient_edad,
            'patient_genero': patient_genero,
            'documents': list(case.documents.all()),  # Convertir QuerySet a lista
            'opiniones': opiniones,
            'opinion_medico_actual': opinion_medico_actual,
            'es_responsable': es_responsable,
            'opinion': getattr(case, 'second_opinion', None),
            'informe_final': informe_final,
            'caso_completado': caso_completado,  # Indica si el caso está completado
            # Debug info
            'debug_docs': [{'id': d.id, 'file_name': d.file_name, 'has_file': bool(d.file), 'file': str(d.file) if d.file else 'None'} for d in case.documents.all()],
            # Antecedentes médicos
            'antecedentes_personales': antecedentes_personales,
            'antecedentes_familiares': antecedentes_familiares,
            'antecedentes_quirurgicos': antecedentes_quirurgicos,
            'alergias': alergias,
            'medicamentos': medicamentos,
        }
        print(f"[DoctorCaseDetailView] Documents for case {case.case_id}:")
        for d in case.documents.all():
            print(f"  - Doc {d.id}: {d.file_name}, has_file={bool(d.file)}, file={d.file}")
        return render(request, self.template_name, context)

    def post(self, request, case_id):
        """Procesa la respuesta del médico sobre el caso (submit de opinión)."""
        if not request.user.is_doctor():
            raise Http404()

        case = get_object_or_404(Case, case_id=case_id)
        if case.doctor != request.user:
            raise Http404("No tienes permiso para modificar este caso.")

        # Extraer campos del formulario
        diagnostico = request.POST.get('diagnostico_propuesto', '').strip()
        tratamiento = request.POST.get('tratamiento_recomendado', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()
        coincide = request.POST.get('coincide') == 'yes'

        # Validación mínima
        if not diagnostico:
            # volver al detalle mostrando error sencillo
            context = {
                'caso': case,
                'case': case,
                'patient_profile': getattr(case.patient, 'patient_profile', None),
                'documents': case.documents.all(),
                'opinion': getattr(case, 'second_opinion', None),
                'error': 'El diagnóstico propuesto es requerido.'
            }
            return render(request, self.template_name, context)

        # Crear opinión final usando el servicio
        try:
            CaseService.complete_case(case, request.user, diagnostico, tratamiento)
            print(f"[DoctorCaseDetailView] Doctor {request.user.email} completó opinión para case {case.case_id}; coincide={coincide}")
        except Exception as e:
            print(f"[DoctorCaseDetailView] Error al completar opinión: {e}")

        # Redirigir al dashboard del médico
        from django.shortcuts import redirect
        return redirect('cases:doctor_dashboard')


def download_document(request, doc_id):
    """Serve CaseDocument file to authorized users (patient, assigned doctor or staff)."""
    from django.contrib.auth.decorators import login_required
    from django.utils.decorators import method_decorator
    from .models import CaseDocument

    @login_required
    def _inner(request, doc_id):
        doc = get_object_or_404(CaseDocument, pk=doc_id)
        case = doc.case
        user = request.user
        allowed = False
        try:
            if user.is_staff:
                allowed = True
            elif hasattr(user, 'patient_cases') and case.patient == user:
                allowed = True
            elif hasattr(user, 'doctor_cases') and case.doctor == user:
                allowed = True
        except Exception:
            allowed = False

        if not allowed:
            raise Http404('No tienes permiso para descargar este documento.')

        try:
            f = doc.file.open('rb')
            # Usar el nombre original del archivo y el tipo MIME
            response = FileResponse(f, as_attachment=True, filename=doc.file_name)
            # Establecer el content-type correcto si está disponible
            if doc.mime_type:
                response['Content-Type'] = doc.mime_type
            return response
        except Exception:
            raise Http404('Archivo no disponible')

    return _inner(request, doc_id)


# =============================================================================
# VISTAS DE MÉDICOS - CASOS (FALTANTES)
# =============================================================================

class CasosPendientesView(LoginRequiredMixin, View):
    """
    Vista para mostrar los casos pendientes de revisión por el médico.
    """
    template_name = 'doctors/casos_pendientes.html'
    login_url = 'auth:login'
    
    def get(self, request):
        if not request.user.is_doctor():
            raise Http404()
        
        from .services import CaseService
        casos_asignados = CaseService.get_doctor_assigned_cases(request.user)
        
        pending_cases = casos_asignados.filter(
            status__in=PENDING_CASE_STATUSES
        ).order_by('-created_at')
        
        context = {
            'casos_pendientes': pending_cases,
            'casos_pendientes_count': pending_cases.count(),
            'user_role': 'doctor'
        }
        return render(request, self.template_name, context)


class MisCasosView(LoginRequiredMixin, View):
    """
    Vista para mostrar todos los casos del médico.
    """
    template_name = 'doctors/mis_casos.html'
    login_url = 'auth:login'
    
    def get(self, request):
        if not request.user.is_doctor():
            raise Http404()
        
        # Usar el servicio para obtener todos los casos del médico (incluye casos del comité)
        # Incluir casos completados
        from .services import CaseService
        all_cases = CaseService.get_doctor_assigned_cases(request.user, include_completed=True)
        
        # Aplicar filtros
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        estado = request.GET.get('estado')
        
        if fecha_desde:
            from datetime import datetime
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                all_cases = all_cases.filter(created_at__gte=fecha_desde_dt)
            except ValueError:
                pass
        
        if fecha_hasta:
            from datetime import datetime
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                # Incluir todo el día
                from django.utils import timezone
                fecha_hasta_dt = timezone.make_aware(fecha_hasta_dt.replace(hour=23, minute=59, second=59))
                all_cases = all_cases.filter(created_at__lte=fecha_hasta_dt)
            except ValueError:
                pass
        
        if estado:
            all_cases = all_cases.filter(status=estado)
        
        all_cases = all_cases.order_by('-created_at')
        
        context = {
            'todos_casos': all_cases,
            'user_role': 'doctor',
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'estado_actual': estado
        }
        return render(request, self.template_name, context)


class ReportesView(LoginRequiredMixin, View):
    """
    Vista para mostrar reportes y estadísticas del médico.
    """
    template_name = 'doctors/reportes.html'
    login_url = 'auth:login'
    
    def get(self, request):
        if not request.user.is_doctor():
            raise Http404()

        from django.utils import timezone
        from .services import CaseService, PENDING_CASE_STATUSES, COMPLETED_CASE_STATUSES

        casos = CaseService.get_doctor_assigned_cases(request.user, include_completed=True)

        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        if fecha_desde:
            casos = casos.filter(created_at__date__gte=fecha_desde)
        if fecha_hasta:
            casos = casos.filter(created_at__date__lte=fecha_hasta)

        casos_pendientes = casos.filter(status__in=PENDING_CASE_STATUSES).count()
        casos_completados = casos.filter(status__in=COMPLETED_CASE_STATUSES).count()

        dias_promedio = 0
        completados = casos.filter(status__in=COMPLETED_CASE_STATUSES, completed_at__isnull=False)
        if completados.exists():
            total_dias = sum(
                (c.completed_at - c.created_at).days for c in completados if c.completed_at and c.created_at
            )
            dias_promedio = round(total_dias / completados.count(), 1)

        context = {
            'total_casos': casos.count(),
            'casos_pendientes_count': casos_pendientes,
            'casos_completados': casos_completados,
            'casos_periodo': casos.order_by('-created_at')[:50],
            'dias_promedio': dias_promedio,
            'fecha_desde': fecha_desde or '',
            'fecha_hasta': fecha_hasta or '',
            'user_role': 'doctor',
        }
        return render(request, self.template_name, context)


# =============================================================================
# CHAT MDT
# =============================================================================

class MDTChatView(LoginRequiredMixin, View):
    """
    Vista para el chat del Comité MDT.
    
    Muestra los grupos médicos (MedicalGroup) a los que pertenece el médico.
    Cada grupo tiene su propio chat donde los miembros pueden interactuar.
    """
    template_name = 'doctors/chat_mdt.html'
    login_url = 'auth:login'
    
    def get(self, request):
        if not request.user.is_doctor():
            raise Http404()
        
        medico = None
        grupos = []
        
        try:
            medico = request.user.medico
            from medicos.models import DoctorGroupMembership
            # Obtener los grupos a los que pertenece el médico
            memberships = DoctorGroupMembership.objects.filter(
                medico=medico,
                activo=True
            ).select_related('grupo')
            
            grupos = [m.grupo for m in memberships if m.grupo.activo]
        except Exception as e:
            print(f"Error getting groups: {e}")
        
        context = {
            'grupos': grupos,
            'grupo': None,
            'mensajes': [],
            'miembros': [],
            'user_role': 'doctor',
            'medico': medico
        }
        return render(request, self.template_name, context)


class MDTChatGrupoView(LoginRequiredMixin, View):
    """
    Vista para el chat de un grupo médico específico.
    Muestra los mensajes del grupo y permite enviar nuevos mensajes.
    """
    template_name = 'doctors/chat_mdt.html'
    login_url = 'auth:login'
    
    def get(self, request, grupo_id):
        if not request.user.is_doctor():
            raise Http404()
        
        medico = None
        grupo = None
        grupos = []
        mensajes = []
        miembros = []
        error_msg = None
        
        try:
            # Obtener médico del usuario
            try:
                medico = request.user.medico
            except Exception:
                error_msg = "No tienes perfil de médico asociado"
                raise Exception(error_msg)
            
            from medicos.models import MedicalGroup, DoctorGroupMembership
            
            # Verificar que el médico pertenece al grupo
            membership = DoctorGroupMembership.objects.filter(
                medico=medico,
                grupo_id=grupo_id,
                activo=True
            ).first()
            
            if not membership:
                error_msg = "No perteneces a este grupo"
                raise Exception(error_msg)
            
            grupo = membership.grupo
            
            # Obtener todos los grupos del médico para la lista lateral
            memberships = DoctorGroupMembership.objects.filter(
                medico=medico,
                activo=True
            ).select_related('grupo')
            grupos = [m.grupo for m in memberships if m.grupo.activo]
            
            # Obtener mensajes del grupo (sin caso específico)
            from .mdt_models import MDTMessage
            mensajes = MDTMessage.objects.filter(
                grupo=grupo,
                caso__isnull=True  # Solo mensajes generales del grupo
            ).select_related('autor').order_by('creado_en')
            
            # Obtener miembros del grupo
            miembros = DoctorGroupMembership.objects.filter(
                grupo=grupo,
                activo=True
            ).select_related('medico')
            
        except Exception as e:
            print(f"Error in MDTChatGrupoView GET: {e}")
        
        context = {
            'grupo': grupo,
            'grupos': grupos,
            'mensajes': mensajes,
            'miembros': miembros,
            'user_role': 'doctor',
            'medico': medico
        }
        return render(request, self.template_name, context)
    
    def post(self, request, grupo_id):
        """Guardar nuevo mensaje en el chat del grupo"""
        if not request.user.is_doctor():
            raise Http404()
        
        mensaje = request.POST.get('mensaje', '').strip()
        
        if mensaje:
            try:
                medico = request.user.medico
                from medicos.models import DoctorGroupMembership
                from .mdt_models import MDTMessage
                
                # Verificar pertenencia al grupo
                membership = DoctorGroupMembership.objects.filter(
                    medico=medico,
                    grupo_id=grupo_id,
                    activo=True
                ).first()
                
                if membership:
                    grupo = membership.grupo
                    
                    # Crear mensaje (sin caso - chat general del grupo)
                    # Usar 0 o un ID válido para caso si es None (problema de FK en SQLite)
                    from cases.models import Case
                    caso_vacio = None
                    try:
                        # Intentar crear sin caso primero
                        MDTMessage.objects.create(
                            grupo=grupo,
                            autor=medico,
                            contenido=mensaje,
                            tipo='mensaje',
                            caso=None  # Chat general
                        )
                    except Exception as e:
                        print(f"Error creating message with caso=None: {e}")
            except Exception as e:
                print(f"Error saving message: {e}")
        
        # Redirect back to the same view
        return HttpResponseRedirect(reverse('cases:mdt_chat_grupo', args=[grupo_id]))


# =============================================================================
# GUÍA DEL SISTEMA
# =============================================================================

class GuiaSistemaView(LoginRequiredMixin, View):
    """
    Vista para la guía del sistema.
    """
    template_name = 'doctors/documentacion.html'
    login_url = 'auth:login'
    
    def get(self, request):
        if not request.user.is_doctor():
            raise Http404()
        
        context = {
            'user_role': 'doctor'
        }
        return render(request, self.template_name, context)


# =============================================================================
# VISTAS MDT - OPINIONES
# =============================================================================

class MedicalOpinionCreateView(LoginRequiredMixin, View):
    """Recibe la opinión/voto del médico (formulario inline en case_detail_modern)."""
    login_url = 'auth:login'

    def get(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        return redirect('cases:doctor_case_detail', case_id=case_id)
    
    def post(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        
        # Obtener el médico
        from medicos.models import Medico
        try:
            medico = Medico.objects.get(usuario=request.user)
        except Medico.DoesNotExist:
            from django.contrib import messages
            messages.error(request, 'No tienes perfil de médico registrado.')
            return redirect('cases:doctor_case_detail', case_id=case_id)
        
        # Procesar opinión
        comentario_privado = request.POST.get('comentario_privado', '').strip()
        voto = request.POST.get('voto', '').strip()
        
        if not comentario_privado or not voto:
            from django.contrib import messages
            messages.error(request, 'Debes escribir tu criterio y seleccionar tu voto.')
            return redirect('cases:doctor_case_detail', case_id=case_id)
        
        # Guardar o actualizar opinión
        from .models import MedicalOpinion
        opinion, created = MedicalOpinion.objects.update_or_create(
            case=case,
            doctor=medico,
            defaults={
                'comentario_privado': comentario_privado,
                'voto': voto
            }
        )
        
        from django.contrib import messages
        messages.success(request, 'Tu opinión ha sido guardada correctamente.')
        
        from django.shortcuts import redirect
        return redirect('cases:doctor_case_detail', case_id=case_id)


class CerrarVotacionView(LoginRequiredMixin, View):
    """Legacy: redirige al detalle del caso."""
    login_url = 'auth:login'

    def post(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        return redirect('cases:doctor_case_detail', case_id=case_id)


class FinalReportCreateView(LoginRequiredMixin, View):
    """Legacy: redirige al detalle del caso (respuesta final vía mdt_response)."""
    login_url = 'auth:login'

    def get(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        return redirect('cases:doctor_case_detail', case_id=case_id)
    
    def post(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        
        # Procesar informe final
        contenido = request.POST.get('contenido', '').strip()
        
        from django.shortcuts import redirect
        return redirect('cases:doctor_dashboard')


# =============================================================================
# VISTAS DE OPINIONES MDT
# =============================================================================

class MDTOpinionView(LoginRequiredMixin, View):
    """Legacy: el voto activo se envía desde case_detail_modern → opinion_form."""
    login_url = 'auth:login'

    def get(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        return redirect('cases:doctor_case_detail', case_id=case_id)
    
    def post(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        medico = request.user.medico
        
        # Obtener o crear workflow
        from .mdt_models import ConsensusWorkflow, ConsensusVote
        workflow, created = ConsensusWorkflow.objects.get_or_create(caso=case)
        
        # Procesar el voto
        voto = request.POST.get('voto', '')
        justificacion = request.POST.get('justificacion', '').strip()
        
        # Guardar o actualizar voto
        vote_obj, vote_created = ConsensusVote.objects.update_or_create(
            workflow=workflow,
            medico=medico,
            defaults={'voto': voto, 'justificacion': justificacion}
        )
        
        # Actualizar contadores del workflow
        workflow.votos_a_favor = ConsensusVote.objects.filter(workflow=workflow, voto__in=['aprueba', 'aprueba_mod']).count()
        workflow.votos_en_contra = ConsensusVote.objects.filter(workflow=workflow, voto__in=['contraindicado', 'alternativa']).count()
        workflow.abstenciones = ConsensusVote.objects.filter(workflow=workflow, voto='abstiene').count()
        workflow.save()
        
        from django.shortcuts import redirect
        return redirect('cases:mdt_opinion', case_id=case_id)


class MDTFinalResponseView(LoginRequiredMixin, View):
    """Genera PDF y envía respuesta final (POST desde case_detail_modern)."""
    login_url = 'auth:login'

    def get(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        return redirect('cases:doctor_case_detail', case_id=case_id)
    
    def post(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        medico = request.user.medico
        
        # Verificar que es responsable
        es_responsable = False
        
        # Primero verificar si es el médico asignado al caso
        if case.doctor == request.user:
            es_responsable = True
        
        # Si no, verificar si es responsable del grupo médico del caso
        if not es_responsable and case.medical_group:
            if hasattr(medico, 'doctorgroupmembership_set'):
                memberships = medico.doctorgroupmembership_set.filter(grupo=case.medical_group)
                es_responsable = any(m.es_responsable for m in memberships)
        
        # Verificar si es el responsable por defecto del grupo
        if not es_responsable and case.medical_group:
            if case.medical_group.responsable_por_defecto == medico:
                es_responsable = True
        
        # Si tampoco, verificar si es el coordinador del comité de la localidad
        if not es_responsable and case.localidad and case.localidad.comite:
            comite = case.localidad.comite
            # Verificar si es miembro del comité Y coordinador
            if hasattr(medico, 'comites'):
                comites_medico = medico.comites.all()
                if comite in comites_medico:
                    # Es miembro - ahora verificar si es coordinador
                    if comite.coordinador == medico:
                        es_responsable = True
        
        if not es_responsable:
            raise Http404("Solo el responsable del comité puede enviar la respuesta final.")
        
        # Procesar respuesta
        conformidad = request.POST.get('conformidad', '')
        explicacion = request.POST.get('explicacion', '').strip() if conformidad == 'no_conformidad' else ''
        
        # Generar PDF y enviar
        from .mdt_services import MDTResponseService
        result = MDTResponseService.generar_y_enviar_respuesta(
            caso=case,
            responsable=medico,
            conformidad=conformidad,
            explicacion=explicacion
        )
        
        if result['success']:
            # Actualizar estado del caso
            case.status = 'OPINION_COMPLETE'
            case.completed_at = timezone.now()
            case.save()
            
            from django.contrib import messages
            messages.success(request, 'Respuesta enviada al paciente correctamente.')
        else:
            from django.contrib import messages
            messages.error(request, f'Error al enviar respuesta: {result.get("error", "Error desconocido")}')
        
        from django.shortcuts import redirect
        return redirect('cases:doctor_dashboard')

def consentimiento_informado_view(request):
    """
    Vista para mostrar el consentimiento informado.
    """
    from django.shortcuts import render
    return render(request, 'public/consentimiento.html', {})
