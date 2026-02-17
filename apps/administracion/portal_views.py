from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
import os

from authentication.models import CustomUser
from authentication.services import DoctorService
from cases.models import Case as CasoMDT, MedicalOpinion
from medicos.models import Medico, Especialidad, Localidad, MedicalGroup
from pacientes.models import Paciente


def _get_admin_credentials():
    email = getattr(settings, 'ADMIN_PORTAL_EMAIL', None)
    password = getattr(settings, 'ADMIN_PORTAL_PASSWORD', None)
    # Fallback: try reading ADMIN_CREDENTIALS.txt in project root
    if not email or not password:
        cred_path = os.path.join(settings.BASE_DIR, 'ADMIN_CREDENTIALS.txt')
        try:
            with open(cred_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('ADMIN_EMAIL='):
                        email = email or line.strip().split('=', 1)[1]
                    if line.startswith('ADMIN_PASSWORD='):
                        password = password or line.strip().split('=', 1)[1]
        except Exception:
            pass
    return email, password


class AdminLoginView(View):
    template_name = 'administracion/portal_login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        admin_email, admin_password = _get_admin_credentials()
        if admin_email and admin_password and email == admin_email and password == admin_password:
            request.session['is_custom_admin'] = True
            return redirect(reverse('administracion:portal_panel'))
        messages.error(request, 'Credenciales inválidas')
        return render(request, self.template_name)


class AdminLogoutView(View):
    def get(self, request):
        request.session.pop('is_custom_admin', None)
        return redirect(reverse('administracion:portal_login'))


from functools import wraps


def admin_required_portal(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        # args may be (request, ...) for function-based views
        # or (self, request, ...) for class-based view methods
        request = None
        if len(args) >= 1 and hasattr(args[0], 'session'):
            request = args[0]
        elif len(args) >= 2 and hasattr(args[1], 'session'):
            request = args[1]

        if request is None:
            return redirect(reverse('administracion:portal_login'))

        if not request.session.get('is_custom_admin'):
            return redirect(reverse('administracion:portal_login'))

        return view_func(*args, **kwargs)

    return wrapped


class AdminPanelView(View):
    template_name = 'administracion/portal_panel.html'

    @admin_required_portal
    def get(self, request):
        # Only one section: Invitar doctores
        return render(request, self.template_name, {'section': 'invite'})


class InviteDoctorView(View):
    @admin_required_portal
    def post(self, request):
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Introduce un correo válido')
            return redirect(reverse('administracion:portal_panel'))

        # Try to find admin user as invited_by
        invited_by = None
        admin_email, _ = _get_admin_credentials()
        if admin_email:
            try:
                invited_by = CustomUser.objects.filter(email=admin_email).first()
            except Exception:
                invited_by = None

        DoctorService.invite_doctor(email, invited_by)
        messages.success(request, f'Invitación enviada a {email} (en cola)')
        return redirect(reverse('administracion:portal_panel'))


# ============================================================================
# NUEVAS VISTAS PARA EL PANEL DE ADMINISTRACIÓN PERSONALIZADO
# ============================================================================

class AdminDashboardView(View):
    """Dashboard principal del panel de administración"""
    template_name = 'admin/dashboard_admin.html'
    
    @admin_required_portal
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
        
        # Casos recientes
        casos_recientes = casos_mdt.order_by('-fecha_creacion')[:10]
        
        context = {
            'stats': stats,
            'casos_recientes': casos_recientes,
        }
        return render(request, self.template_name, context)


class GestionCasosView(View):
    """Lista de todos los casos del sistema"""
    template_name = 'admin/casos_list.html'
    
    @admin_required_portal
    def get(self, request):
        # Filtrar por estado
        estado = request.GET.get('estado')
        search = request.GET.get('search')
        
        casos = CasoMDT.objects.all().select_related('paciente', 'paciente__user', 'especialidad', 'localidad')
        
        if estado:
            casos = casos.filter(status=estado)
        if search:
            casos = casos.filter(
                Q(case_id__icontains=search) |
                Q(paciente__user__email__icontains=search)
            )
        
        casos = casos.order_by('-fecha_creacion')
        
        context = {
            'casos': casos,
            'estado_actual': estado,
        }
        return render(request, self.template_name, context)


class CasoDetalleView(View):
    """Detalle de un caso específico"""
    template_name = 'admin/caso_detalle.html'
    
    @admin_required_portal
    def get(self, request, case_id):
        caso = get_object_or_404(CasoMDT, case_id=case_id)
        opiniones = MedicalOpinion.objects.filter(caso=caso).select_related('medico', 'medico__user')
        
        context = {
            'caso': caso,
            'opiniones': opiniones,
        }
        return render(request, self.template_name, context)


class AsignarCasoView(View):
    """Asignar caso a un médico"""
    template_name = 'admin/caso_asignar.html'
    
    @admin_required_portal
    def get(self, request, case_id):
        caso = get_object_or_404(CasoMDT, case_id=case_id)
        medicos = Medico.objects.filter(estado='activo').select_related('usuario')
        
        context = {
            'caso': caso,
            'medicos': medicos,
        }
        return render(request, self.template_name, context)
    
    @admin_required_portal
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
    
    @admin_required_portal
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
    
    @admin_required_portal
    def get(self, request, medico_id):
        medico = get_object_or_404(Medico, id=medico_id)
        casos = CasoMDT.objects.filter(medico_asignado=medico).order_by('-fecha_creacion')[:10]
        
        context = {
            'medico': medico,
            'casos': casos,
        }
        return render(request, self.template_name, context)


class GestionPacientesView(View):
    """Lista de todos los pacientes"""
    template_name = 'admin/pacientes_list.html'
    
    @admin_required_portal
    def get(self, request):
        search = request.GET.get('search')
        
        pacientes = Paciente.objects.select_related('user')
        
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
    
    @admin_required_portal
    def get(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, id=paciente_id)
        casos = CasoMDT.objects.filter(paciente=paciente).order_by('-fecha_creacion')
        
        context = {
            'paciente': paciente,
            'casos': casos,
        }
        return render(request, self.template_name, context)


class GestionComitesView(View):
    """Lista de comités MDT"""
    template_name = 'admin/comites_list.html'
    
    @admin_required_portal
    def get(self, request):
        comites = MedicalGroup.objects.select_related('especialidad', 'localidad').prefetch_related('miembros', 'miembros__user')
        
        context = {
            'comites': comites,
        }
        return render(request, self.template_name, context)


class ConfiguracionView(View):
    """Configuración del sistema"""
    template_name = 'admin/configuracion.html'
    
    @admin_required_portal
    def get(self, request):
        especialidades = Especialidad.objects.all()
        localidades = Localidad.objects.all()
        
        context = {
            'especialidades': especialidades,
            'localidades': localidades,
        }
        return render(request, self.template_name, context)
