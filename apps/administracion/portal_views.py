from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
import os

from authentication.models import CustomUser
from authentication.services import DoctorService
from cases.models import Case as CasoMDT, MedicalOpinion
from medicos.models import Medico, Especialidad, Localidad, MedicalGroup
from pacientes.models import Paciente
from core.decorators import admin_required


# ============================================================================
# NUEVAS VISTAS PARA EL PANEL DE ADMINISTRACIÓN PERSONALIZADO
# ============================================================================

class AdminDashboardView(View):
    """Dashboard principal del panel de administración"""
    template_name = 'admin/dashboard_admin.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        # Estadísticas del sistema
        casos_mdt = CasoMDT.objects.all()
        
        stats = {
            'total_casos': casos_mdt.count(),
            'casos_pendientes': casos_mdt.filter(status='PENDIENTE').count(),
            'casos_proceso': casos_mdt.filter(status='EN_PROCESO').count(),
            'casos_completados': casos_mdt.filter(status='COMPLETADO').count(),
            'medicos_activos': Medico.objects.filter(estado='activo').count(),
            'pacientes': Paciente.objects.filter(activo=True).count(),
            'comites': MedicalGroup.objects.filter(activo=True).count(),
        }
        
        # Casos recientes - select_related para acceder al paciente
        casos_recientes = casos_mdt.select_related('patient').order_by('-created_at')[:10]
        
        context = {
            'stats': stats,
            'casos_recientes': casos_recientes,
        }
        return render(request, self.template_name, context)


class GestionCasosView(View):
    """Lista de todos los casos del sistema"""
    template_name = 'admin/casos_list.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        # Filtrar por estado
        estado = request.GET.get('estado')
        search = request.GET.get('search')
        
        casos = CasoMDT.objects.all().select_related('patient', 'medical_group', 'responsable', 'localidad')
        
        if estado:
            casos = casos.filter(status=estado)
        if search:
            casos = casos.filter(
                Q(case_id__icontains=search) |
                Q(paciente__user__email__icontains=search)
            )
        
        casos = casos.order_by('-created_at')
        
        context = {
            'casos': casos,
            'estado_actual': estado,
        }
        return render(request, self.template_name, context)


class CasoDetalleView(View):
    """Detalle de un caso específico"""
    template_name = 'admin/caso_detalle.html'
    
    @method_decorator(admin_required)
    def get(self, request, case_id):
        caso = get_object_or_404(CasoMDT, case_id=case_id)
        opiniones = MedicalOpinion.objects.filter(caso=caso).select_related('doctor', 'doctor__usuario')
        
        context = {
            'caso': caso,
            'opiniones': opiniones,
        }
        return render(request, self.template_name, context)


class AsignarCasoView(View):
    """Asignar caso a un médico"""
    template_name = 'admin/caso_asignar.html'
    
    @method_decorator(admin_required)
    def get(self, request, case_id):
        caso = get_object_or_404(CasoMDT, case_id=case_id)
        medicos = Medico.objects.filter(estado='activo').select_related('usuario')
        
        context = {
            'caso': caso,
            'medicos': medicos,
        }
        return render(request, self.template_name, context)
    
    @method_decorator(admin_required)
    def post(self, request, case_id):
        caso = get_object_or_404(CasoMDT, case_id=case_id)
        medico_id = request.POST.get('medico_id')
        
        if medico_id:
            medico = get_object_or_404(Medico, id=medico_id)
            caso.asignar_medico(medico)
            messages.success(request, f'Caso asignado a {medico.user.get_full_name()}')
        
        return redirect(reverse('administracion:portal_caso_detalle', args=[case_id]))


class GestionMedicosView(View):
    """Lista de todos los médicos"""
    template_name = 'admin/medicos_list.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        search = request.GET.get('search')
        especialidad = request.GET.get('especialidad')
        
        medicos = Medico.objects.select_related('usuario').prefetch_related('especialidades')
        
        if search:
            medicos = medicos.filter(
                Q(usuario__email__icontains=search) |
                Q(nombres__icontains=search) |
                Q(apellidos__icontains=search)
            )
        if especialidad:
            medicos = medicos.filter(especialidades__id=especialidad)
        
        especialidades = Especialidad.objects.filter(activa=True)
        
        context = {
            'medicos': medicos,
            'especialidades': especialidades,
        }
        return render(request, self.template_name, context)


class MedicoDetalleView(View):
    """Detalle de un médico específico"""
    template_name = 'admin/medico_detalle.html'
    
    @method_decorator(admin_required)
    def get(self, request, medico_id):
        medico = get_object_or_404(Medico, id=medico_id)
        casos = CasoMDT.objects.filter(medico_asignado=medico).order_by('-created_at')[:10]
        
        context = {
            'medico': medico,
            'casos': casos,
        }
        return render(request, self.template_name, context)


class GestionPacientesView(View):
    """Lista de todos los pacientes"""
    template_name = 'admin/pacientes_list.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        search = request.GET.get('search')
        
        pacientes = Paciente.objects.select_related('usuario')
        
        if search:
            pacientes = pacientes.filter(
                Q(user__email__icontains=search) |
                Q(numero_documento__icontains=search)
            )
        
        context = {
            'pacientes': pacientes,
        }
        return render(request, self.template_name, context)


class PacienteDetalleView(View):
    """Detalle de un paciente específico"""
    template_name = 'admin/paciente_detalle.html'
    
    @method_decorator(admin_required)
    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, id=paciente_id)
        casos = CasoMDT.objects.filter(paciente=paciente).order_by('-created_at')
        
        context = {
            'paciente': paciente,
            'casos': casos,
        }
        return render(request, self.template_name, context)


class GestionComitesView(View):
    """Lista de comités MDT"""
    template_name = 'admin/comites_list.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        comites = MedicalGroup.objects.select_related('responsable_por_defecto').prefetch_related('miembros', 'miembros__medico__usuario', 'tipos_cancer')
        
        context = {
            'comites': comites,
        }
        return render(request, self.template_name, context)


class ConfiguracionView(View):
    """Configuración del sistema"""
    template_name = 'admin/configuracion.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        especialidades = Especialidad.objects.all()
        localidades = Localidad.objects.all()
        
        context = {
            'especialidades': especialidades,
            'localidades': localidades,
        }
        return render(request, self.template_name, context)


class InviteDoctorView(View):
    """Vista para invitar médicos al sistema"""
    
    @method_decorator(admin_required)
    def post(self, request):
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Introduce un correo válido')
            return redirect(reverse('administracion:portal_dashboard'))

        # Usar el usuario actual como invitado por
        invited_by = request.user

        try:
            DoctorService.invite_doctor(email, invited_by)
            messages.success(request, f'Invitación enviada a {email}')
        except Exception as e:
            messages.error(request, f'Error al enviar invitación: {str(e)}')
        
        return redirect(reverse('administracion:portal_dashboard'))
