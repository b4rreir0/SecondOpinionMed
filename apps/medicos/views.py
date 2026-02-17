# medicos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Medico, RevisionCaso, ComiteMultidisciplinario, ReunionComite, DisponibilidadMedico
from .forms import RevisionCasoForm, ReunionComiteForm, DisponibilidadMedicoForm
from core.decorators import medico_required
from core.services import AsignacionService, NotificacionService, ComiteService
from pacientes.models import Paciente
from cases.models import Case
from cases.services import CaseService

@medico_required
def dashboard(request):
    """Dashboard del médico"""
    medico = request.user.medico
    
    # Casos asignados al médico (usando CaseService que incluye casos del comité)
    casos_asignados = CaseService.get_doctor_assigned_cases(request.user)
    casos_pendientes = casos_asignados.filter(status='IN_REVIEW')
    
    # Casos revisados este mes
    casos_revisados_mes = casos_asignados.filter(
        status='COMPLETED'
    ).count()
    
    # Reuniones de comité
    casos_comite = ReunionComite.objects.filter(
        medicos_participantes=medico,
        fecha_programada__gte=timezone.now()
    ).count()
    
    # Casos pendientes de revisión (usando CaseService)
    casos_pendientes_list = casos_pendientes.order_by('-created_at')[:5]
    
    # Próximas reuniones de comité
    reuniones_proximas = ReunionComite.objects.filter(
        medicos_participantes=medico,
        fecha_programada__gte=timezone.now()
    ).order_by('fecha_programada')[:3]
    
    context = {
        'medico': medico,
        'casos_asignados': casos_asignados,
        'casos_revisados_mes': casos_revisados_mes,
        'casos_comite': casos_comite,
        'casos_pendientes': casos_pendientes_list,
        'reuniones_proximas': reuniones_proximas,
        'capacidad_disponible': medico.capacidad_disponible,
    }
    
    return render(request, 'medicos/dashboard.html', context)

@medico_required
def perfil(request):
    """Vista del perfil del médico"""
    medico = request.user.medico
    
    if request.method == 'POST':
        # Procesar actualización de perfil
        medico.telefono = request.POST.get('telefono', medico.telefono)
        medico.institucion_actual = request.POST.get('institucion_actual', medico.institucion_actual)
        medico.save()
        
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('medicos:perfil')
    
    return render(request, 'medicos/perfil.html', {'medico': medico})

@medico_required
def casos_asignados(request):
    """Lista de casos asignados al médico"""
    medico = request.user.medico
    
    # Filtros
    estado = request.GET.get('estado', 'asignado')
    prioridad = request.GET.get('prioridad')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    casos = CasoClinico.objects.filter(medico_asignado=medico)
    
    if estado:
        casos = casos.filter(estado=estado)
    if prioridad:
        casos = casos.filter(prioridad=prioridad)
    if fecha_desde:
        casos = casos.filter(fecha_asignacion__date__gte=fecha_desde)
    if fecha_hasta:
        casos = casos.filter(fecha_asignacion__date__lte=fecha_hasta)
    
    casos = casos.order_by('-fecha_asignacion')
    
    # Paginación
    paginator = Paginator(casos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estado': estado,
        'prioridad': prioridad,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'medicos/casos_asignados.html', context)

@medico_required
def caso_detail(request, uuid):
    """Detalle de un caso asignado"""
    medico = request.user.medico
    caso = get_object_or_404(CasoClinico, uuid=uuid, medico_asignado=medico)
    
    # Verificar si ya existe una revisión del médico
    revision_existente = RevisionCaso.objects.filter(caso=caso, medico=medico).first()
    
    # Documentos del caso
    documentos = caso.documentos.all()
    
    # Historial de revisiones
    revisiones = caso.revisiones.all().order_by('-creado_en')
    
    context = {
        'caso': caso,
        'revision_existente': revision_existente,
        'documentos': documentos,
        'revisiones': revisiones,
    }
    
    return render(request, 'medicos/caso_detail.html', context)

@medico_required
@csrf_protect
def revision_create(request, caso_uuid):
    """Crear revisión de caso"""
    medico = request.user.medico
    caso = get_object_or_404(CasoClinico, uuid=caso_uuid, medico_asignado=medico)
    
    # Verificar que no exista ya una revisión
    if RevisionCaso.objects.filter(caso=caso, medico=medico).exists():
        messages.warning(request, 'Ya has realizado una revisión para este caso.')
        return redirect('medicos:caso_detail', uuid=caso.uuid)
    
    if request.method == 'POST':
        form = RevisionCasoForm(request.POST)
        if form.is_valid():
            revision = form.save(commit=False)
            revision.caso = caso
            revision.medico = medico
            revision.save()
            
            # Actualizar estado del caso
            caso.estado = 'en_revision'
            caso.save()
            
            # Notificar al paciente con detalles de la revisión
            NotificacionService.notificar_paciente_revision(caso, revision)
            
            messages.success(request, 'Revisión guardada exitosamente.')
            return redirect('medicos:caso_detail', uuid=caso.uuid)
    else:
        form = RevisionCasoForm()
    
    return render(request, 'medicos/revision_form.html', {'form': form, 'caso': caso})

@medico_required
@csrf_protect
def revision_edit(request, caso_uuid, revision_pk):
    """Editar revisión de caso"""
    medico = request.user.medico
    caso = get_object_or_404(CasoClinico, uuid=caso_uuid, medico_asignado=medico)
    revision = get_object_or_404(RevisionCaso, pk=revision_pk, caso=caso, medico=medico)
    
    if request.method == 'POST':
        form = RevisionCasoForm(request.POST, instance=revision)
        if form.is_valid():
            form.save()
            messages.success(request, 'Revisión actualizada exitosamente.')
            return redirect('medicos:caso_detail', uuid=caso.uuid)
    else:
        form = RevisionCasoForm(instance=revision)
    
    return render(request, 'medicos/revision_form.html', {'form': form, 'caso': caso, 'revision': revision})

@medico_required
@require_http_methods(["POST"])
def revision_complete(request, caso_uuid, revision_pk):
    """Marcar revisión como completada"""
    medico = request.user.medico
    caso = get_object_or_404(CasoClinico, uuid=caso_uuid, medico_asignado=medico)
    revision = get_object_or_404(RevisionCaso, pk=revision_pk, caso=caso, medico=medico)
    
    revision.completar_revision()
    
    # Verificar si el caso debe ir a comité
    if revision.requiere_discusion:
        ComiteService.asignar_a_comite(caso)
        messages.success(request, 'Revisión completada. Caso enviado a comité multidisciplinario.')
    else:
        caso.estado = 'concluido'
        caso.fecha_conclusion = timezone.now()
        caso.save()
        messages.success(request, 'Revisión completada exitosamente.')
    
    return redirect('medicos:caso_detail', uuid=caso.uuid)

@medico_required
def comites_list(request):
    """Lista de comités del médico"""
    medico = request.user.medico
    
    comites = ComiteMultidisciplinario.objects.filter(medicos_miembros=medico)
    
    # Reuniones próximas
    reuniones_proximas = ReunionComite.objects.filter(
        comite__in=comites,
        fecha_programada__gte=timezone.now()
    ).order_by('fecha_programada')
    
    context = {
        'comites': comites,
        'reuniones_proximas': reuniones_proximas,
    }
    
    return render(request, 'medicos/comites_list.html', context)

@medico_required
def reunion_detail(request, pk):
    """Detalle de reunión de comité"""
    medico = request.user.medico
    reunion = get_object_or_404(
        ReunionComite,
        pk=pk,
        medicos_participantes=medico
    )
    
    context = {
        'reunion': reunion,
        'caso': reunion.caso,
    }
    
    return render(request, 'medicos/reunion_detail.html', context)

@medico_required
@csrf_protect
def disponibilidad_manage(request):
    """Gestionar disponibilidad del médico"""
    medico = request.user.medico
    
    if request.method == 'POST':
        form = DisponibilidadMedicoForm(request.POST)
        if form.is_valid():
            disponibilidad = form.save(commit=False)
            disponibilidad.medico = medico
            disponibilidad.save()
            
            messages.success(request, 'Disponibilidad registrada exitosamente.')
            return redirect('medicos:disponibilidad_manage')
    else:
        form = DisponibilidadMedicoForm()
    
    # Disponibilidad actual
    disponibilidad_actual = DisponibilidadMedico.objects.filter(
        medico=medico,
        activo=True
    ).order_by('dia_semana', 'hora_inicio')
    
    context = {
        'form': form,
        'disponibilidad_actual': disponibilidad_actual,
    }
    
    return render(request, 'medicos/disponibilidad_manage.html', context)

@medico_required
@require_http_methods(["POST"])
def disponibilidad_delete(request, pk):
    """Eliminar disponibilidad"""
    medico = request.user.medico
    disponibilidad = get_object_or_404(DisponibilidadMedico, pk=pk, medico=medico)
    
    disponibilidad.activo = False
    disponibilidad.save()
    
    messages.success(request, 'Disponibilidad eliminada exitosamente.')
    return redirect('medicos:disponibilidad_manage')

@medico_required
def estadisticas_personales(request):
    """Estadísticas personales del médico"""
    medico = request.user.medico
    
    # Estadísticas mensuales
    mes_actual = timezone.now().month
    anio_actual = timezone.now().year
    
    casos_mes = CasoClinico.objects.filter(
        medico_asignado=medico,
        fecha_asignacion__month=mes_actual,
        fecha_asignacion__year=anio_actual
    ).count()
    
    revisiones_mes = RevisionCaso.objects.filter(
        medico=medico,
        creado_en__month=mes_actual,
        creado_en__year=anio_actual
    ).count()
    
    reuniones_mes = ReunionComite.objects.filter(
        medicos_participantes=medico,
        fecha_programada__month=mes_actual,
        fecha_programada__year=anio_actual
    ).count()
    
    context = {
        'medico': medico,
        'casos_mes': casos_mes,
        'revisiones_mes': revisiones_mes,
        'reuniones_mes': reuniones_mes,
    }
    
    return render(request, 'medicos/estadisticas.html', context)
