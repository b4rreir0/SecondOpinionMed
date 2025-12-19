# pacientes/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Paciente, CasoClinico, AntecedenteMedico, DocumentoClinico, SolicitudSegundaOpinion
from .forms import CasoClinicoForm, AntecedenteMedicoForm, DocumentoClinicoForm, SolicitudSegundaOpinionForm
from core.decorators import paciente_required
from core.services import NotificacionService
from medicos.models import Localidad

@paciente_required
def dashboard(request):
    """Dashboard del paciente"""
    paciente = request.user.paciente
    
    # Estadísticas del paciente
    casos_totales = CasoClinico.objects.filter(paciente=paciente).count()
    casos_activos = CasoClinico.objects.filter(
        paciente=paciente, 
        estado__in=['enviado', 'asignado', 'en_revision', 'comite']
    ).count()
    casos_concluidos = CasoClinico.objects.filter(
        paciente=paciente, 
        estado='concluido'
    ).count()
    
    # Casos recientes
    casos_recientes = CasoClinico.objects.filter(paciente=paciente).order_by('-creado_en')[:5]
    
    context = {
        'paciente': paciente,
        'casos_totales': casos_totales,
        'casos_activos': casos_activos,
        'casos_concluidos': casos_concluidos,
        'casos_recientes': casos_recientes,
    }
    
    return render(request, 'pacientes/dashboard.html', context)

@paciente_required
def perfil(request):
    """Vista del perfil del paciente"""
    paciente = request.user.paciente
    
    if request.method == 'POST':
        # Procesar actualización de perfil
        paciente.telefono = request.POST.get('telefono', paciente.telefono)
        paciente.direccion = request.POST.get('direccion', paciente.direccion)
        paciente.ocupacion = request.POST.get('ocupacion', paciente.ocupacion)
        paciente.save()
        
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('pacientes:perfil')
    
    return render(request, 'pacientes/perfil.html', {'paciente': paciente})

@paciente_required
def casos_list(request):
    """Lista de casos clínicos del paciente"""
    paciente = request.user.paciente
    
    # Filtros
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    casos = CasoClinico.objects.filter(paciente=paciente)
    
    if estado:
        casos = casos.filter(estado=estado)
    if fecha_desde:
        casos = casos.filter(creado_en__date__gte=fecha_desde)
    if fecha_hasta:
        casos = casos.filter(creado_en__date__lte=fecha_hasta)
    
    casos = casos.order_by('-creado_en')
    
    # Paginación
    paginator = Paginator(casos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'pacientes/casos_list.html', context)

@paciente_required
@csrf_protect
def caso_create(request):
    """Crear nuevo caso clínico"""
    paciente = request.user.paciente
    
    if request.method == 'POST':
        form = CasoClinicoForm(request.POST)
        if form.is_valid():
            caso = form.save(commit=False)
            caso.paciente = paciente
            caso.save()
            
            messages.success(request, 'Caso clínico creado exitosamente.')
            return redirect('pacientes:caso_detail', uuid=caso.uuid)
    else:
        form = CasoClinicoForm()
    
    return render(request, 'pacientes/caso_form.html', {'form': form})

@paciente_required
def caso_detail(request, uuid):
    """Detalle de un caso clínico"""
    paciente = request.user.paciente
    caso = get_object_or_404(CasoClinico, uuid=uuid, paciente=paciente)
    
    # Documentos del caso
    documentos = caso.documentos.all()
    
    context = {
        'caso': caso,
        'documentos': documentos,
    }
    
    return render(request, 'pacientes/caso_detail.html', context)

@paciente_required
@csrf_protect
def caso_edit(request, uuid):
    """Editar caso clínico"""
    paciente = request.user.paciente
    caso = get_object_or_404(CasoClinico, uuid=uuid, paciente=paciente)
    
    # Solo permitir edición si está en borrador
    if caso.estado != 'borrador':
        messages.error(request, 'No se puede editar un caso que ya ha sido enviado.')
        return redirect('pacientes:caso_detail', uuid=caso.uuid)
    
    if request.method == 'POST':
        form = CasoClinicoForm(request.POST, instance=caso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Caso clínico actualizado exitosamente.')
            return redirect('pacientes:caso_detail', uuid=caso.uuid)
    else:
        form = CasoClinicoForm(instance=caso)
    
    return render(request, 'pacientes/caso_form.html', {'form': form, 'caso': caso})

@paciente_required
@require_http_methods(["POST"])
def caso_send(request, uuid):
    """Enviar caso para revisión"""
    paciente = request.user.paciente
    caso = get_object_or_404(CasoClinico, uuid=uuid, paciente=paciente)
    
    if caso.estado != 'borrador':
        messages.error(request, 'El caso ya ha sido enviado.')
        return redirect('pacientes:caso_detail', uuid=caso.uuid)
    
    caso.estado = 'enviado'
    caso.fecha_envio = timezone.now()
    caso.save()
    
    # Notificar al sistema
    NotificacionService.notificar_caso_enviado(caso)
    
    messages.success(request, 'Caso enviado exitosamente para revisión.')
    return redirect('pacientes:caso_detail', uuid=caso.uuid)

@paciente_required
def antecedentes_list(request):
    """Lista de antecedentes médicos"""
    paciente = request.user.paciente
    antecedentes = AntecedenteMedico.objects.filter(paciente=paciente).order_by('-fecha_diagnostico')
    
    return render(request, 'pacientes/antecedentes_list.html', {'antecedentes': antecedentes})

@paciente_required
@csrf_protect
def antecedente_create(request):
    """Crear antecedente médico"""
    paciente = request.user.paciente
    
    if request.method == 'POST':
        form = AntecedenteMedicoForm(request.POST)
        if form.is_valid():
            antecedente = form.save(commit=False)
            antecedente.paciente = paciente
            antecedente.save()
            
            messages.success(request, 'Antecedente médico registrado exitosamente.')
            return redirect('pacientes:antecedentes_list')
    else:
        form = AntecedenteMedicoForm()
    
    return render(request, 'pacientes/antecedente_form.html', {'form': form})

@paciente_required
@csrf_protect
def antecedente_edit(request, pk):
    """Editar antecedente médico"""
    paciente = request.user.paciente
    antecedente = get_object_or_404(AntecedenteMedico, pk=pk, paciente=paciente)
    
    if request.method == 'POST':
        form = AntecedenteMedicoForm(request.POST, instance=antecedente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Antecedente médico actualizado exitosamente.')
            return redirect('pacientes:antecedentes_list')
    else:
        form = AntecedenteMedicoForm(instance=antecedente)
    
    return render(request, 'pacientes/antecedente_form.html', {'form': form, 'antecedente': antecedente})

@paciente_required
@csrf_protect
def documento_upload(request, caso_uuid):
    """Subir documento clínico"""
    paciente = request.user.paciente
    caso = get_object_or_404(CasoClinico, uuid=caso_uuid, paciente=paciente)
    
    if request.method == 'POST':
        form = DocumentoClinicoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.caso = caso
            documento.save()
            
            messages.success(request, 'Documento subido exitosamente.')
            return redirect('pacientes:caso_detail', uuid=caso.uuid)
    else:
        form = DocumentoClinicoForm()
    
    return render(request, 'pacientes/documento_upload.html', {'form': form, 'caso': caso})

@paciente_required
@csrf_protect
def solicitud_segunda_opinion(request, caso_uuid):
    """Crear solicitud de segunda opinión"""
    paciente = request.user.paciente
    caso = get_object_or_404(CasoClinico, uuid=caso_uuid, paciente=paciente)
    
    # Verificar si ya existe una solicitud
    if hasattr(caso, 'solicitud'):
        messages.warning(request, 'Ya existe una solicitud de segunda opinión para este caso.')
        return redirect('pacientes:caso_detail', uuid=caso.uuid)
    
    if request.method == 'POST':
        form = SolicitudSegundaOpinionForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.caso = caso
            solicitud.save()
            # If a localidad was provided, link it to the caso and assign the doctor
            localidad = form.cleaned_data.get('localidad')
            if localidad:
                caso.localidad = localidad
                caso.save()
                if localidad.medico:
                    try:
                        caso.asignar_medico(localidad.medico)
                        # Notify assigned doctor
                        NotificacionService.notificar_asignacion_caso(caso, localidad.medico)
                    except Exception:
                        # fallback: ignore notification errors but keep flow
                        pass
            
            messages.success(request, 'Solicitud de segunda opinión enviada exitosamente.')
            return redirect('pacientes:caso_detail', uuid=caso.uuid)
    else:
        form = SolicitudSegundaOpinionForm()
    
    return render(request, 'pacientes/solicitud_form.html', {'form': form, 'caso': caso})
