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
from cases.models import Case as CasoMDT, MedicalOpinion, CaseDocument
from medicos.models import Medico, Especialidad, Localidad, MedicalGroup, TipoCancer, DoctorGroupMembership
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
        opiniones = MedicalOpinion.objects.filter(case=caso).select_related('doctor', 'doctor__usuario')
        documentos = CaseDocument.objects.filter(case=caso).order_by('-uploaded_at')
        
        context = {
            'caso': caso,
            'opiniones': opiniones,
            'documentos': documentos,
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
        casos = CasoMDT.objects.filter(responsable=medico).order_by('-created_at')[:10]
        grupos = MedicalGroup.objects.filter(miembros__medico=medico, miembros__activo=True)
        
        context = {
            'medico': medico,
            'casos': casos,
            'grupos': grupos,
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
                Q(usuario__email__icontains=search) |
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
        casos = CasoMDT.objects.filter(patient=paciente.usuario).order_by('-created_at')
        
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
    template_name = 'admin/invite_doctor.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        return render(request, self.template_name)
    
    @method_decorator(admin_required)
    def post(self, request):
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Introduce un correo válido')
            return redirect(reverse('administracion:portal_invite'))

        # Usar el usuario actual como invitado por
        invited_by = request.user

        try:
            DoctorService.invite_doctor(email, invited_by)
            messages.success(request, f'Invitación enviada a {email}')
            return redirect(reverse('administracion:portal_medicos'))
        except Exception as e:
            messages.error(request, f'Error al enviar invitación: {str(e)}')
        
        return redirect(reverse('administracion:portal_invite'))


# ============================================================================
# GESTIÓN DE TIPOS DE CÁNCER
# ============================================================================

class GestionTiposCancerView(View):
    """Lista de tipos de cáncer del sistema"""
    template_name = 'admin/tipos_cancer_list.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        search = request.GET.get('search')
        grupo = request.GET.get('grupo')
        
        tipos = TipoCancer.objects.select_related('especialidad_principal', 'grupo_medico')
        
        if search:
            tipos = tipos.filter(
                Q(nombre__icontains=search) |
                Q(codigo__icontains=search)
            )
        if grupo:
            tipos = tipos.filter(grupo_medico__id=grupo)
        
        grupos = MedicalGroup.objects.filter(activo=True)
        especialidades = Especialidad.objects.filter(activa=True)
        
        context = {
            'tipos_cancer': tipos,
            'grupos': grupos,
            'especialidades': especialidades,
        }
        return render(request, self.template_name, context)


class TipoCancerCrearView(View):
    """Crear un nuevo tipo de cáncer"""
    template_name = 'admin/tipo_cancer_form.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        grupos = MedicalGroup.objects.filter(activo=True)
        especialidades = Especialidad.objects.filter(activa=True)
        
        context = {
            'tipo_cancer': None,
            'grupos': grupos,
            'especialidades': especialidades,
            'action': 'Crear'
        }
        return render(request, self.template_name, context)
    
    @method_decorator(admin_required)
    def post(self, request):
        nombre = request.POST.get('nombre')
        codigo = request.POST.get('codigo').upper()
        descripcion = request.POST.get('descripcion')
        especialidad_id = request.POST.get('especialidad_principal')
        grupo_id = request.POST.get('grupo_medico')
        activo = request.POST.get('activo') == 'on'
        
        if TipoCancer.objects.filter(codigo=codigo).exists():
            messages.error(request, 'Ya existe un tipo de cáncer con ese código')
            return redirect(reverse('administracion:portal_tipos_cancer'))
        
        especialidad = None
        if especialidad_id:
            especialidad = get_object_or_404(Especialidad, id=especialidad_id)
        
        grupo = None
        if grupo_id:
            grupo = get_object_or_404(MedicalGroup, id=grupo_id)
        
        TipoCancer.objects.create(
            nombre=nombre,
            codigo=codigo,
            descripcion=descripcion,
            especialidad_principal=especialidad,
            grupo_medico=grupo,
            activo=activo
        )
        
        messages.success(request, f'Tipo de cáncer "{nombre}" creado exitosamente')
        return redirect(reverse('administracion:portal_tipos_cancer'))


class TipoCancerEditarView(View):
    """Editar un tipo de cáncer"""
    template_name = 'admin/tipo_cancer_form.html'
    
    @method_decorator(admin_required)
    def get(self, request, tipo_id):
        tipo = get_object_or_404(TipoCancer, id=tipo_id)
        grupos = MedicalGroup.objects.filter(activo=True)
        especialidades = Especialidad.objects.filter(activa=True)
        
        context = {
            'tipo_cancer': tipo,
            'grupos': grupos,
            'especialidades': especialidades,
            'action': 'Editar'
        }
        return render(request, self.template_name, context)
    
    @method_decorator(admin_required)
    def post(self, request, tipo_id):
        tipo = get_object_or_404(TipoCancer, id=tipo_id)
        
        nombre = request.POST.get('nombre')
        codigo = request.POST.get('codigo').upper()
        descripcion = request.POST.get('descripcion')
        especialidad_id = request.POST.get('especialidad_principal')
        grupo_id = request.POST.get('grupo_medico')
        activo = request.POST.get('activo') == 'on'
        
        # Verificar código duplicado (excluyendo el actual)
        if TipoCancer.objects.exclude(id=tipo_id).filter(codigo=codigo).exists():
            messages.error(request, 'Ya existe otro tipo de cáncer con ese código')
            return redirect(reverse('administracion:portal_tipo_cancer_editar', args=[tipo_id]))
        
        tipo.nombre = nombre
        tipo.codigo = codigo
        tipo.descripcion = descripcion
        tipo.activo = activo
        
        if especialidad_id:
            tipo.especialidad_principal = get_object_or_404(Especialidad, id=especialidad_id)
        else:
            tipo.especialidad_principal = None
        
        if grupo_id:
            tipo.grupo_medico = get_object_or_404(MedicalGroup, id=grupo_id)
        else:
            tipo.grupo_medico = None
        
        tipo.save()
        
        messages.success(request, f'Tipo de cáncer "{nombre}" actualizado exitosamente')
        return redirect(reverse('administracion:portal_tipos_cancer'))


class TipoCancerEliminarView(View):
    """Eliminar un tipo de cáncer"""
    
    @method_decorator(admin_required)
    def post(self, request, tipo_id):
        tipo = get_object_or_404(TipoCancer, id=tipo_id)
        nombre = tipo.nombre
        tipo.delete()
        messages.success(request, f'Tipo de cáncer "{nombre}" eliminado')
        return redirect(reverse('administracion:portal_tipos_cancer'))


# ============================================================================
# GESTIÓN DE GRUPOS MÉDICOS / COMITÉS
# ============================================================================

class GestionGruposView(View):
    """Lista de grupos médicos del sistema"""
    template_name = 'admin/grupos_list.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        search = request.GET.get('search')
        
        grupos = MedicalGroup.objects.select_related('responsable_por_defecto').prefetch_related('tipos_cancer', 'miembros', 'miembros__medico')
        
        if search:
            grupos = grupos.filter(nombre__icontains=search)
        
        context = {
            'grupos': grupos,
        }
        return render(request, self.template_name, context)


class GrupoCrearView(View):
    """Crear un nuevo grupo médico"""
    template_name = 'admin/grupo_form.html'
    
    @method_decorator(admin_required)
    def get(self, request):
        medicos = Medico.objects.filter(estado='activo').select_related('usuario')
        tipos = TipoCancer.objects.filter(activo=True)
        
        context = {
            'grupo': None,
            'medicos': medicos,
            'tipos_cancer': tipos,
            'action': 'Crear'
        }
        return render(request, self.template_name, context)
    
    @method_decorator(admin_required)
    def post(self, request):
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        responsable_id = request.POST.get('responsable_por_defecto')
        quorum = int(request.POST.get('quorum_config', 3))
        activo = request.POST.get('activo') == 'on'
        
        if MedicalGroup.objects.filter(nombre=nombre).exists():
            messages.error(request, 'Ya existe un grupo con ese nombre')
            return redirect(reverse('administracion:portal_grupos'))
        
        responsable = None
        if responsable_id:
            responsable = get_object_or_404(Medico, id=responsable_id)
        
        grupo = MedicalGroup.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            responsable_por_defecto=responsable,
            quorum_config=quorum,
            activo=activo
        )
        
        messages.success(request, f'Grupo médico "{nombre}" creado exitosamente')
        return redirect(reverse('administracion:portal_grupos'))


class GrupoEditarView(View):
    """Editar un grupo médico"""
    template_name = 'admin/grupo_form.html'
    
    @method_decorator(admin_required)
    def get(self, request, grupo_id):
        grupo = get_object_or_404(MedicalGroup, id=grupo_id)
        medicos = Medico.objects.filter(estado='activo').select_related('usuario')
        tipos = TipoCancer.objects.filter(activo=True)
        
        context = {
            'grupo': grupo,
            'medicos': medicos,
            'tipos_cancer': tipos,
            'action': 'Editar'
        }
        return render(request, self.template_name, context)
    
    @method_decorator(admin_required)
    def post(self, request, grupo_id):
        grupo = get_object_or_404(MedicalGroup, id=grupo_id)
        
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        responsable_id = request.POST.get('responsable_por_defecto')
        quorum = int(request.POST.get('quorum_config', 3))
        activo = request.POST.get('activo') == 'on'
        
        # Verificar nombre duplicado
        if MedicalGroup.objects.exclude(id=grupo_id).filter(nombre=nombre).exists():
            messages.error(request, 'Ya existe otro grupo con ese nombre')
            return redirect(reverse('administracion:portal_grupo_editar', args=[grupo_id]))
        
        grupo.nombre = nombre
        grupo.descripcion = descripcion
        grupo.quorum_config = quorum
        grupo.activo = activo
        
        if responsable_id:
            grupo.responsable_por_defecto = get_object_or_404(Medico, id=responsable_id)
        else:
            grupo.responsable_por_defecto = None
        
        grupo.save()
        
        messages.success(request, f'Grupo médico "{nombre}" actualizado exitosamente')
        return redirect(reverse('administracion:portal_grupos'))


class GrupoDetalleView(View):
    """Detalle de un grupo médico con gestión de miembros"""
    template_name = 'admin/grupo_detalle.html'
    
    @method_decorator(admin_required)
    def get(self, request, grupo_id):
        grupo = get_object_or_404(MedicalGroup, id=grupo_id)
        membresias = DoctorGroupMembership.objects.filter(grupo=grupo).select_related('medico', 'medico__usuario')
        medicos_no_members = Medico.objects.filter(estado='activo').exclude(
            id__in=membresias.values('medico_id')
        ).select_related('usuario')
        
        # Tipos de cáncer disponibles (que no están asignados a ningún grupo o al actual)
        tipos_asignados = TipoCancer.objects.filter(grupo_medico=grupo)
        tipos_disponibles = TipoCancer.objects.filter(activo=True).exclude(
            id__in=tipos_asignados.values('id')
        ).exclude(grupo_medico__isnull=False)
        
        context = {
            'grupo': grupo,
            'membresias': membresias,
            'medicos_no_members': medicos_no_members,
            'tipos_asignados': tipos_asignados,
            'tipos_disponibles': tipos_disponibles,
        }
        return render(request, self.template_name, context)


class GrupoAgregarMiembroView(View):
    """Agregar un médico a un grupo"""
    
    @method_decorator(admin_required)
    def post(self, request, grupo_id):
        grupo = get_object_or_404(MedicalGroup, id=grupo_id)
        medico_id = request.POST.get('medico_id')
        rol = request.POST.get('rol', 'miembro_regular')
        es_responsable = request.POST.get('es_responsable') == 'on'
        
        medico = get_object_or_404(Medico, id=medico_id)
        
        # Verificar si ya es miembro
        if DoctorGroupMembership.objects.filter(medico=medico, grupo=grupo).exists():
            messages.error(request, f'{medico.nombre_completo} ya es miembro del grupo')
        else:
            DoctorGroupMembership.objects.create(
                medico=medico,
                grupo=grupo,
                rol=rol,
                es_responsable=es_responsable,
                activo=True
            )
            messages.success(request, f'{medico.nombre_completo} agregado al grupo')
        
        return redirect(reverse('administracion:portal_grupo_detalle', args=[grupo_id]))


class GrupoEliminarMiembroView(View):
    """Eliminar un médico de un grupo"""
    
    @method_decorator(admin_required)
    def post(self, request, grupo_id):
        membresia_id = request.POST.get('membresia_id')
        membresia = get_object_or_404(DoctorGroupMembership, id=membresia_id, grupo_id=grupo_id)
        nombre = membresia.medico.nombre_completo
        membresia.delete()
        messages.success(request, f'{nombre} eliminado del grupo')
        return redirect(reverse('administracion:portal_grupo_detalle', args=[grupo_id]))


class GrupoAsignarTipoCancerView(View):
    """Asignar un tipo de cáncer a un grupo"""
    
    @method_decorator(admin_required)
    def post(self, request, grupo_id):
        grupo = get_object_or_404(MedicalGroup, id=grupo_id)
        tipo_id = request.POST.get('tipo_id')
        tipo = get_object_or_404(TipoCancer, id=tipo_id)
        
        # Verificar si ya tiene grupo asignado
        if tipo.grupo_medico and tipo.grupo_medico.id != grupo.id:
            messages.error(request, f'El tipo de cáncer "{tipo.nombre}" ya está asignado a otro grupo')
        else:
            tipo.grupo_medico = grupo
            tipo.save()
            messages.success(request, f'Tipo de cáncer "{tipo.nombre}" asignado al grupo')
        
        return redirect(reverse('administracion:portal_grupo_detalle', args=[grupo_id]))


class GrupoQuitarTipoCancerView(View):
    """Quitar un tipo de cáncer de un grupo"""
    
    @method_decorator(admin_required)
    def post(self, request, grupo_id):
        tipo_id = request.POST.get('tipo_id')
        tipo = get_object_or_404(TipoCancer, id=tipo_id, grupo_medico_id=grupo_id)
        nombre = tipo.nombre
        tipo.grupo_medico = None
        tipo.save()
        messages.success(request, f'Tipo de cáncer "{nombre}" quitado del grupo')
        return redirect(reverse('administracion:portal_grupo_detalle', args=[grupo_id]))


class GrupoEliminarView(View):
    """Eliminar un grupo médico"""
    
    @method_decorator(admin_required)
    def post(self, request, grupo_id):
        grupo = get_object_or_404(MedicalGroup, id=grupo_id)
        nombre = grupo.nombre
        grupo.delete()
        messages.success(request, f'Grupo médico "{nombre}" eliminado')
        return redirect(reverse('administracion:portal_grupos'))
