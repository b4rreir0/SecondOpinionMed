# administracion/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from .models import Administrador, ConfiguracionSistema, ReporteSistema, NotificacionSistema, BackupSistema, LogSistema
from .forms import ConfiguracionSistemaForm, NotificacionSistemaForm, ReporteSistemaForm
from core.decorators import admin_required
from core.services import AsignacionService, ReporteService, AuditoriaService
from pacientes.models import Paciente, CasoClinico
from medicos.models import Medico, ComiteMultidisciplinario
from django.contrib.auth.models import User

@admin_required
def dashboard(request):
    """Dashboard del administrador"""
    admin = request.user.administrador
    
    # Estadísticas generales
    total_pacientes = Paciente.objects.filter(activo=True).count()
    total_medicos = Medico.objects.filter(estado='activo').count()
    total_casos = CasoClinico.objects.count()
    casos_activos = CasoClinico.objects.filter(
        estado__in=['enviado', 'asignado', 'en_revision', 'comite']
    ).count()
    
    # Casos por estado
    casos_por_estado = CasoClinico.objects.values('estado').annotate(
        count=Count('estado')
    ).order_by('estado')
    
    # Actividad reciente
    casos_recientes = CasoClinico.objects.order_by('-creado_en')[:5]
    
    # Alertas del sistema
    alertas = []
    if casos_activos > total_medicos * 5:  # Más de 5 casos por médico
        alertas.append({
            'tipo': 'warning',
            'mensaje': 'Alta carga de trabajo. Considere contratar más médicos.'
        })
    
    casos_sin_asignar = CasoClinico.objects.filter(estado='enviado', medico_asignado__isnull=True).count()
    if casos_sin_asignar > 0:
        alertas.append({
            'tipo': 'info',
            'mensaje': f'{casos_sin_asignar} casos esperando asignación.'
        })
    
    context = {
        'admin': admin,
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
        'total_casos': total_casos,
        'casos_activos': casos_activos,
        'casos_por_estado': casos_por_estado,
        'casos_recientes': casos_recientes,
        'alertas': alertas,
    }
    
    return render(request, 'administracion/dashboard.html', context)

@admin_required
def pacientes_list(request):
    """Lista de pacientes"""
    # Filtros
    search = request.GET.get('search')
    estado = request.GET.get('estado', 'activo')
    
    pacientes = Paciente.objects.all()
    
    if estado == 'activo':
        pacientes = pacientes.filter(activo=True)
    elif estado == 'inactivo':
        pacientes = pacientes.filter(activo=False)
    
    if search:
        pacientes = pacientes.filter(
            Q(nombres__icontains=search) |
            Q(apellidos__icontains=search) |
            Q(numero_documento__icontains=search) |
            Q(email_alternativo__icontains=search)
        )
    
    pacientes = pacientes.order_by('apellidos', 'nombres')
    
    # Paginación
    paginator = Paginator(pacientes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'estado': estado,
    }
    
    return render(request, 'administracion/pacientes_list.html', context)

@admin_required
def paciente_detail(request, pk):
    """Detalle de paciente"""
    paciente = get_object_or_404(Paciente, pk=pk)
    
    # Casos del paciente
    casos = CasoClinico.objects.filter(paciente=paciente).order_by('-creado_en')
    
    # Antecedentes
    antecedentes = paciente.antecedentes.all().order_by('-fecha_diagnostico')
    
    context = {
        'paciente': paciente,
        'casos': casos,
        'antecedentes': antecedentes,
    }
    
    return render(request, 'administracion/paciente_detail.html', context)

@admin_required
@require_http_methods(["POST"])
def paciente_toggle_status(request, pk):
    """Activar/desactivar paciente"""
    paciente = get_object_or_404(Paciente, pk=pk)
    
    paciente.activo = not paciente.activo
    if not paciente.activo:
        paciente.fecha_inactivacion = timezone.now()
    else:
        paciente.fecha_inactivacion = None
    paciente.save()
    
    status_text = "activado" if paciente.activo else "desactivado"
    messages.success(request, f'Paciente {status_text} exitosamente.')
    
    AuditoriaService.registrar_accion(
        usuario=request.user,
        tipo_accion='modificacion',
        modelo_afectado='Paciente',
        objeto_id=paciente.pk,
        descripcion=f"Paciente {status_text}"
    )
    
    return redirect('administracion:paciente_detail', pk=pk)

@admin_required
def medicos_list(request):
    """Lista de médicos"""
    # Filtros
    search = request.GET.get('search')
    estado = request.GET.get('estado')
    especialidad = request.GET.get('especialidad')
    
    medicos = Medico.objects.all()
    
    if estado:
        medicos = medicos.filter(estado=estado)
    if especialidad:
        medicos = medicos.filter(especialidades__id=especialidad)
    
    if search:
        medicos = medicos.filter(
            Q(nombres__icontains=search) |
            Q(apellidos__icontains=search) |
            Q(registro_medico__icontains=search)
        )
    
    medicos = medicos.order_by('apellidos', 'nombres')
    
    # Paginación
    paginator = Paginator(medicos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Especialidades para filtro
    from medicos.models import Especialidad
    especialidades = Especialidad.objects.filter(activa=True)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'estado': estado,
        'especialidad': especialidad,
        'especialidades': especialidades,
    }
    
    return render(request, 'administracion/medicos_list.html', context)

@admin_required
def medico_detail(request, pk):
    """Detalle de médico"""
    medico = get_object_or_404(Medico, pk=pk)
    
    # Casos asignados
    casos_asignados = CasoClinico.objects.filter(medico_asignado=medico).order_by('-fecha_asignacion')
    
    # Revisiones realizadas
    revisiones = medico.revisiones.all().order_by('-creado_en')[:10]
    
    # Estadísticas
    casos_mes = CasoClinico.objects.filter(
        medico_asignado=medico,
        fecha_asignacion__month=timezone.now().month,
        fecha_asignacion__year=timezone.now().year
    ).count()
    
    context = {
        'medico': medico,
        'casos_asignados': casos_asignados,
        'revisiones': revisiones,
        'casos_mes': casos_mes,
    }
    
    return render(request, 'administracion/medico_detail.html', context)

@admin_required
@require_http_methods(["POST"])
def medico_toggle_status(request, pk):
    """Activar/desactivar médico"""
    medico = get_object_or_404(Medico, pk=pk)
    
    if medico.estado == 'activo':
        medico.estado = 'suspendido'
    else:
        medico.estado = 'activo'
    medico.save()
    
    status_text = "activado" if medico.estado == 'activo' else "suspendido"
    messages.success(request, f'Médico {status_text} exitosamente.')
    
    AuditoriaService.registrar_accion(
        usuario=request.user,
        tipo_accion='modificacion',
        modelo_afectado='Medico',
        objeto_id=medico.pk,
        descripcion=f"Médico {status_text}"
    )
    
    return redirect('administracion:medico_detail', pk=pk)

@admin_required
def casos_list(request):
    """Lista de todos los casos"""
    # Filtros
    search = request.GET.get('search')
    estado = request.GET.get('estado')
    prioridad = request.GET.get('prioridad')
    medico = request.GET.get('medico')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    casos = CasoClinico.objects.select_related('paciente', 'medico_asignado')
    
    if estado:
        casos = casos.filter(estado=estado)
    if prioridad:
        casos = casos.filter(prioridad=prioridad)
    if medico:
        casos = casos.filter(medico_asignado__id=medico)
    if fecha_desde:
        casos = casos.filter(creado_en__date__gte=fecha_desde)
    if fecha_hasta:
        casos = casos.filter(creado_en__date__lte=fecha_hasta)
    
    if search:
        casos = casos.filter(
            Q(titulo__icontains=search) |
            Q(paciente__nombres__icontains=search) |
            Q(paciente__apellidos__icontains=search) |
            Q(uuid__icontains=search)
        )
    
    casos = casos.order_by('-creado_en')
    
    # Paginación
    paginator = Paginator(casos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Médicos para filtro
    medicos = Medico.objects.filter(estado='activo')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'estado': estado,
        'prioridad': prioridad,
        'medico': medico,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'medicos': medicos,
    }
    
    return render(request, 'administracion/casos_list.html', context)

@admin_required
def caso_detail_admin(request, uuid):
    """Detalle administrativo de caso"""
    caso = get_object_or_404(CasoClinico, uuid=uuid)
    
    # Revisiones del caso
    revisiones = caso.revisiones.all().order_by('-creado_en')
    
    # Documentos
    documentos = caso.documentos.all()
    
    context = {
        'caso': caso,
        'revisiones': revisiones,
        'documentos': documentos,
    }
    
    return render(request, 'administracion/caso_detail.html', context)

@admin_required
@require_http_methods(["POST"])
def caso_assign_medico(request, uuid):
    """Asignar médico a caso"""
    caso = get_object_or_404(CasoClinico, uuid=uuid)
    medico_id = request.POST.get('medico_id')
    
    if medico_id:
        medico = get_object_or_404(Medico, pk=medico_id, estado='activo')
        AsignacionService.asignar_caso_medico(caso)  # Usar el servicio automático
        
        messages.success(request, f'Caso asignado a Dr. {medico.nombre_completo}')
        
        AuditoriaService.registrar_accion(
            usuario=request.user,
            tipo_accion='modificacion',
            modelo_afectado='CasoClinico',
            objeto_id=caso.pk,
            descripcion=f"Asignado a médico {medico.nombre_completo}"
        )
    
    return redirect('administracion:caso_detail', uuid=uuid)

@admin_required
def configuracion_sistema(request):
    """Configuración del sistema"""
    if request.method == 'POST':
        form = ConfiguracionSistemaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada exitosamente.')
            return redirect('administracion:configuracion_sistema')
    else:
        form = ConfiguracionSistemaForm()
    
    # Configuraciones existentes
    configuraciones = ConfiguracionSistema.objects.all().order_by('tipo', 'clave')
    
    context = {
        'form': form,
        'configuraciones': configuraciones,
    }
    
    return render(request, 'administracion/configuracion_sistema.html', context)

@admin_required
def reportes_list(request):
    """Lista de reportes del sistema"""
    reportes = ReporteSistema.objects.all().order_by('-ultima_ejecucion')
    
    context = {
        'reportes': reportes,
    }
    
    return render(request, 'administracion/reportes_list.html', context)

@admin_required
@require_http_methods(["POST"])
def ejecutar_reporte(request, pk):
    """Ejecutar reporte"""
    reporte = get_object_or_404(ReporteSistema, pk=pk)
    
    try:
        # Aquí iría la lógica para ejecutar el reporte específico
        reporte.ultima_ejecucion = timezone.now()
        reporte.ejecuciones_exitosas += 1
        reporte.save()
        
        messages.success(request, f'Reporte "{reporte.nombre}" ejecutado exitosamente.')
    except Exception as e:
        reporte.ejecuciones_fallidas += 1
        reporte.save()
        messages.error(request, f'Error ejecutando reporte: {str(e)}')
    
    return redirect('administracion:reportes_list')

@admin_required
def auditoria_list(request):
    """Lista de registros de auditoría"""
    from core.models import Auditoria
    
    # Filtros
    usuario = request.GET.get('usuario')
    tipo_accion = request.GET.get('tipo_accion')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    auditoria = Auditoria.objects.select_related('usuario')
    
    if usuario:
        auditoria = auditoria.filter(usuario__username__icontains=usuario)
    if tipo_accion:
        auditoria = auditoria.filter(tipo_accion=tipo_accion)
    if fecha_desde:
        auditoria = auditoria.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        auditoria = auditoria.filter(fecha__date__lte=fecha_hasta)
    
    auditoria = auditoria.order_by('-fecha')
    
    # Paginación
    paginator = Paginator(auditoria, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'usuario': usuario,
        'tipo_accion': tipo_accion,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'administracion/auditoria_list.html', context)

@admin_required
def notificaciones_list(request):
    """Lista de notificaciones del sistema"""
    notificaciones = NotificacionSistema.objects.all().order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(notificaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'administracion/notificaciones_list.html', context)

@admin_required
@csrf_protect
def notificacion_create(request):
    """Crear notificación del sistema"""
    if request.method == 'POST':
        form = NotificacionSistemaForm(request.POST)
        if form.is_valid():
            notificacion = form.save(commit=False)
            notificacion.creada_por = request.user
            notificacion.save()
            
            messages.success(request, 'Notificación creada exitosamente.')
            return redirect('administracion:notificaciones_list')
    else:
        form = NotificacionSistemaForm()
    
    return render(request, 'administracion/notificacion_form.html', {'form': form})

@admin_required
def estadisticas_generales(request):
    """Estadísticas generales del sistema"""
    # Estadísticas de casos
    casos_por_mes = CasoClinico.objects.extra(
        select={'month': "EXTRACT(month FROM creado_en)", 'year': "EXTRACT(year FROM creado_en)"}
    ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')
    
    # Estadísticas por especialidad
    from medicos.models import RevisionCaso
    especialidades_stats = RevisionCaso.objects.values(
        'medico__especialidades__nombre'
    ).annotate(count=Count('id')).order_by('-count')[:10]
    
    # Rendimiento de médicos
    medicos_rendimiento = Medico.objects.filter(estado='activo').values(
        'nombres', 'apellidos', 'casos_revisados'
    ).order_by('-casos_revisados')[:10]
    
    context = {
        'casos_por_mes': casos_por_mes,
        'especialidades_stats': especialidades_stats,
        'medicos_rendimiento': medicos_rendimiento,
    }
    
    return render(request, 'administracion/estadisticas_generales.html', context)
