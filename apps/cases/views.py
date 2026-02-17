from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.http import FileResponse

from .models import Case
from .services import CaseService


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
        if not request.user.is_patient():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        
        # OLP: Verificar que el usuario es el paciente del caso
        if case.patient != request.user:
            raise Http404("No tienes permiso para ver este caso.")
        
        # Registrar acceso
        CaseService.log_case_access(case, request.user, 'read')

        # Si el caso está asignado a este médico pero aún no está en IN_REVIEW,
        # marcarlo como en revisión cuando el médico abra el detalle.
        try:
            if case.doctor == request.user and case.status != 'IN_REVIEW':
                case.status = 'IN_REVIEW'
                from django.utils import timezone
                case.assigned_at = timezone.now()
                case.save()
                print(f"[DoctorCaseDetailView] Case {case.case_id} viewed by doctor {request.user.email}; status set to IN_REVIEW")
                CaseService.log_case_access(case, request.user, 'update')
        except Exception:
            pass
        
        context = {
            'case': case,
            'documents': case.documents.all(),
            'opinion': getattr(case, 'second_opinion', None)
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
            status__in=['PAID', 'IN_REVIEW', 'CLARIFICATION_NEEDED', 'ASSIGNED', 'PROCESSING']
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
        
        # 2. Si es miembro del comité de la localidad del caso
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
        
        # Calcular edad del paciente (a través de patient_profile)
        patient_edad = None
        patient_genero = None
        patient_nombre = None
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
            patient_genero = None
        
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
        except Exception:
            opinion_medico_actual = None
            es_responsable = False
        
        context = {
            'caso': case,  # Usar 'caso' para compatibilidad con el template
            'case': case,  # También mantener 'case'
            'patient_profile': case.patient.patient_profile,
            'patient_nombre': patient_nombre,
            'patient_edad': patient_edad,
            'patient_genero': patient_genero,
            'documents': case.documents.all(),
            'opiniones': opiniones,
            'opinion_medico_actual': opinion_medico_actual,
            'es_responsable': es_responsable,
            'opinion': getattr(case, 'second_opinion', None),
            # Antecedentes médicos
            'antecedentes_personales': antecedentes_personales,
            'antecedentes_familiares': antecedentes_familiares,
            'antecedentes_quirurgicos': antecedentes_quirurgicos,
            'alergias': alergias,
            'medicamentos': medicamentos,
        }
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
        
        # DEBUG: Log para verificar
        print(f"[CasosPendientes] Usuario: {request.user.email}")
        print(f"[CasosPendientes] Es doctor: {request.user.is_doctor()}")
        
        # DEBUG: Ver todos los casos en la base de datos
        from .models import Case
        todos_casos = Case.objects.all()
        print(f"[CasosPendientes] TOTAL casos en BD: {todos_casos.count()}")
        for c in todos_casos:
            print(f"  - {c.case_id}: status={c.status}, doctor={c.doctor}, localidad={c.localidad}")
        
        # Usar el servicio para obtener los casos asignados al médico (incluye casos del comité)
        from .services import CaseService
        casos_asignados = CaseService.get_doctor_assigned_cases(request.user)
        print(f"[CasosPendientes] Casos asignados (sin filtro): {casos_asignados.count()}")
        
        pending_cases = casos_asignados.filter(
            status__in=['PAID', 'IN_REVIEW', 'CLARIFICATION_NEEDED', 'ASSIGNED', 'PROCESSING']
        ).order_by('-created_at')
        
        print(f"[CasosPendientes] Casos pendientes (filtrados): {pending_cases.count()}")
        print(f"[CasosPendientes] Estados posibles: {list(pending_cases.values_list('status', flat=True))}")
        
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
        
        from .models import Case
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        # Estadísticas básicas
        total_cases = Case.objects.filter(doctor=request.user).count()
        completed_cases = Case.objects.filter(doctor=request.user, status='completed').count()
        pending_cases = Case.objects.filter(doctor=request.user, status__in=['pending', 'in_progress']).count()
        
        # Casos del último mes
        last_month = datetime.now() - timedelta(days=30)
        cases_this_month = Case.objects.filter(
            doctor=request.user,
            created_at__gte=last_month
        ).count()
        
        context = {
            'total_cases': total_cases,
            'completed_cases': completed_cases,
            'pending_cases': pending_cases,
            'cases_this_month': cases_this_month,
            'user_role': 'doctor'
        }
        return render(request, self.template_name, context)


# =============================================================================
# CHAT MDT
# =============================================================================

class MDTChatView(LoginRequiredMixin, View):
    """
    Vista para el chat del Comité MDT.
    """
    template_name = 'doctors/chat_mdt.html'
    login_url = 'auth:login'
    
    def get(self, request):
        if not request.user.is_doctor():
            raise Http404()
        
        # Por ahora, obtener todos los comités MDT disponibles
        try:
            from medicos.models import ComiteMultidisciplinario
            committees = ComiteMultidisciplinario.objects.all()
        except Exception:
            committees = []
        
        context = {
            'committees': committees,
            'user_role': 'doctor'
        }
        return render(request, self.template_name, context)


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
    """
    Vista para crear una opinión médica en un caso MDT.
    """
    template_name = 'doctors/opinion_form.html'
    login_url = 'auth:login'
    
    def get(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        
        context = {
            'case': case,
            'user_role': 'doctor'
        }
        return render(request, self.template_name, context)
    
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


class OpinionSummaryView(LoginRequiredMixin, View):
    """
    Vista para mostrar el resumen de opiniones de un caso MDT.
    """
    template_name = 'doctors/opinion_summary.html'
    login_url = 'auth:login'
    
    def get(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        
        context = {
            'case': case,
            'user_role': 'doctor'
        }
        return render(request, self.template_name, context)


class CerrarVotacionView(LoginRequiredMixin, View):
    """
    Vista para cerrar la votación de un caso MDT.
    """
    login_url = 'auth:login'
    
    def post(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        
        # Cerrar votación (simplificado)
        # En un caso real, esto cerraría la votación en el modelo correspondiente
        
        from django.shortcuts import redirect
        return redirect('cases:doctor_dashboard')


class FinalReportCreateView(LoginRequiredMixin, View):
    """
    Vista para crear el informe final de un caso.
    """
    template_name = 'doctors/report_form.html'
    login_url = 'auth:login'
    
    def get(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        
        context = {
            'case': case,
            'user_role': 'doctor'
        }
        return render(request, self.template_name, context)
    
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
    """
    Vista para que los miembros del comité emitan su opinión sobre un caso.
    """
    template_name = 'doctors/mdt_opinion.html'
    login_url = 'auth:login'
    
    def get(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        medico = request.user.medico
        
        # Obtener o crear workflow de consenso
        from .mdt_models import ConsensusWorkflow, ConsensusVote
        workflow, created = ConsensusWorkflow.objects.get_or_create(caso=case)
        
        # Obtener el voto actual del médico si existe
        voto_existente = ConsensusVote.objects.filter(workflow=workflow, medico=medico).first()
        
        # Obtener todos los votos
        todos_votos = ConsensusVote.objects.filter(workflow=workflow)
        
        context = {
            'case': case,
            'workflow': workflow,
            'voto_existente': voto_existente,
            'todos_votos': todos_votos,
            'user_role': 'doctor',
            'medico': medico
        }
        return render(request, self.template_name, context)
    
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
    """
    Vista para que el responsable/coordinador envíe la respuesta final al paciente.
    """
    template_name = 'doctors/mdt_final_response.html'
    login_url = 'auth:login'
    
    def get(self, request, case_id):
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        medico = request.user.medico
        
        # Obtener workflow
        from .mdt_models import ConsensusWorkflow, ConsensusVote
        try:
            workflow = case.workflow_consenso
        except ConsensusWorkflow.DoesNotExist:
            workflow = ConsensusWorkflow.objects.create(caso=case)
        
        # Obtener todos los votos
        todos_votos = ConsensusVote.objects.filter(workflow=workflow)
        
        # Verificar si es responsable
        es_responsable = False
        
        # Primero verificar si es el médico asignado al caso
        if case.doctor == request.user:
            es_responsable = True
        
        # Si no, verificar si es responsable del grupo médico del caso
        if not es_responsable and case.medical_group:
            if hasattr(medico, 'doctorgroupmembership_set'):
                memberships = medico.doctorgroupmembership_set.filter(grupo=case.medical_group)
                es_responsable = any(m.es_responsable for m in memberships)
        
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
        
        context = {
            'case': case,
            'workflow': workflow,
            'todos_votos': todos_votos,
            'user_role': 'doctor',
            'medico': medico,
            'es_responsable': es_responsable
        }
        return render(request, self.template_name, context)
    
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
            case.status = 'COMPLETED'
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
