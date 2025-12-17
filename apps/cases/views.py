from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

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
