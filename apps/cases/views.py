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
    template_name = 'doctors/dashboard.html'
    login_url = 'auth:login'
    
    def get(self, request):
        """Muestra el dashboard del médico"""
        if not request.user.is_doctor():
            return redirect('/')
        
        # OLP: Solo obtener casos asignados al médico
        assigned_cases = CaseService.get_doctor_assigned_cases(request.user)
        
        context = {
            'cases': assigned_cases,
            'user_role': 'doctor',
            'doctor_profile': request.user.doctor_profile
        }
        return render(request, self.template_name, context)


class DoctorCaseDetailView(LoginRequiredMixin, View):
    """
    Detalle de un caso para el Médico.
    
    Muestra todos los detalles y documentos del caso.
    OLP: Verifica que el usuario sea el médico asignado.
    """
    template_name = 'doctors/case_detail.html'
    login_url = 'auth:login'
    
    def get(self, request, case_id):
        """Muestra detalle del caso"""
        if not request.user.is_doctor():
            raise Http404()
        
        case = get_object_or_404(Case, case_id=case_id)
        
        # OLP: Verificar que el usuario es el médico asignado
        if case.doctor != request.user:
            raise Http404("No tienes permiso para ver este caso.")
        
        # Registrar acceso
        CaseService.log_case_access(case, request.user, 'read')
        
        context = {
            'case': case,
            'patient_profile': case.patient.patient_profile,
            'documents': case.documents.all(),
            'opinion': getattr(case, 'second_opinion', None)
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
            resp = FileResponse(f, as_attachment=True, filename=doc.file_name)
            return resp
        except Exception:
            raise Http404('Archivo no disponible')

    return _inner(request, doc_id)
