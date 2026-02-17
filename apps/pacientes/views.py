# pacientes/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseRedirect, Http404
from django.http import FileResponse
from .models import Paciente, CasoClinico, AntecedenteMedico, DocumentoClinico, SolicitudSegundaOpinion
from .forms import CasoClinicoForm, AntecedenteMedicoForm, DocumentoClinicoForm, SolicitudSegundaOpinionForm
from core.decorators import paciente_required
from core.services import NotificacionService
from medicos.models import Localidad
from cases.models import Case, MedicalOpinion, FinalReport

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


# ==== Nuevas vistas para el sistema MDT ====

@paciente_required
def dashboard_paciente(request):
    """Dashboard moderno del paciente con el nuevo sistema MDT"""
    paciente = request.user
    
    # Buscar casos en el modelo Case (Sistema MDT)
    from cases.models import Case, MedicalOpinion
    casos_case = Case.objects.filter(patient=paciente).order_by('-created_at')
    
    # También buscar en CasoMDT si existe
    try:
        from cases.mdt_models import CasoMDT
        casos_mdt = CasoMDT.objects.filter(paciente=paciente).order_by('-fecha_creacion')
    except:
        casos_mdt = []
    
    # Combinar casos
    casos = casos_case
    
    # Estadísticas
    casos_count = casos.count()
    casos_pendientes = casos.filter(status__in=['SUBMITTED', 'ASSIGNED', 'PROCESSING', 'MDT_IN_PROGRESS']).count()
    casos_completados = casos.filter(status__in=['MDT_COMPLETED', 'REPORT_DRAFT', 'REPORT_COMPLETE', 'OPINION_COMPLETE', 'CLOSED']).count()
    
    # Contar opiniones médicas recibidas
    opiniones_recibidas = MedicalOpinion.objects.filter(
        case__patient=paciente
    ).count()
    
    # Obtener informes finales
    from cases.models import FinalReport
    informes = FinalReport.objects.filter(case__patient=paciente).order_by('-fecha_emision')[:3]
    
    # Obtener algunos casos para mostrar (limit 5)
    casos_recientes = casos[:5]
    
    # Actividades recientes - casos con actividad
    actividades = []
    for c in casos[:3]:
        actividades.append({
            'tipo': 'ESTADO',
            'titulo': f'Caso {c.case_id} actualizado',
            'fecha': c.updated_at,
            'descripcion': c.get_status_display()
        })
    
    context = {
        'casos': casos_recientes,
        'casos_count': casos_count,
        'casos_pendientes': casos_pendientes,
        'casos_completados': casos_completados,
        'opiniones_recibidas': opiniones_recibidas,
        'informes': informes,
        'actividades_recientes': actividades,
    }
    
    return render(request, 'patients/dashboard_patient.html', context)


@paciente_required
def detalle_caso_paciente(request, case_id):
    """Detalle de un caso para el paciente"""
    from cases.models import Case, MedicalOpinion, FinalReport
    
    paciente = request.user
    
    # Buscar primero en Case (nuevo sistema)
    caso = Case.objects.filter(patient=paciente, case_id=case_id).first()
    
    if not caso:
        # Buscar en CasoMDT (sistema antiguo)
        try:
            from cases.mdt_models import CasoMDT
            caso = CasoMDT.objects.filter(paciente=paciente, case_id=case_id).first()
            es_caso_mdt = True
        except:
            es_caso_mdt = False
    else:
        es_caso_mdt = False
    
    if not caso:
        raise Http404("Caso no encontrado")
    
    # Obtener opiniones médicas según el tipo de caso
    if es_caso_mdt:
        try:
            from cases.mdt_models import CasoMDT
            opiniones = MedicalOpinion.objects.filter(caso=caso).select_related('medico', 'medico__user')
        except:
            opiniones = []
    else:
        opiniones = MedicalOpinion.objects.filter(case=caso).select_related('doctor', 'doctor__user')
    
    # Obtener informes
    informes = FinalReport.objects.filter(case=caso).order_by('-fecha_emision')[:3] if not es_caso_mdt else []
    
    # Timeline de eventos
    if es_caso_mdt:
        timeline = [
            {
                'titulo': 'Caso Creado',
                'descripcion': 'Se recibió la documentación clínica',
                'fecha': caso.fecha_creacion,
                'icono': 'add_circle',
                'completado': True,
                'actual': False,
            },
            {
                'titulo': 'En Revisión',
                'descripcion': 'Médicos especialistas evaluando tu caso',
                'fecha': caso.fecha_asignacion or caso.fecha_creacion,
                'icono': 'rate_review',
                'completado': caso.status in ['EN_PROCESO', 'COMPLETADO'],
                'actual': caso.status == 'EN_PROCESO',
            },
            {
                'titulo': 'Opiniones Médicas',
                'descripcion': f'{opiniones.count()} opiniones recibidas',
                'fecha': caso.fecha_creacion,
                'icono': 'medical_information',
                'completado': caso.status == 'COMPLETADO',
                'actual': False,
            },
        ]
    else:
        # Timeline para el modelo Case
        timeline = [
            {
                'titulo': 'Caso Creado',
                'descripcion': 'Se recibió la documentación clínica',
                'fecha': caso.created_at,
                'icono': 'add_circle',
                'completado': True,
                'actual': False,
            },
            {
                'titulo': 'En Revisión',
                'descripcion': 'Médicos especialistas evaluando tu caso',
                'fecha': caso.created_at,
                'icono': 'rate_review',
                'completado': caso.status in ['ASSIGNED', 'PROCESSING', 'MDT_IN_PROGRESS', 'MDT_COMPLETED'],
                'actual': caso.status == 'MDT_IN_PROGRESS',
            },
            {
                'titulo': 'Opiniones Médicas',
                'descripcion': f'{opiniones.count()} opiniones recibidas',
                'fecha': caso.created_at,
                'icono': 'medical_information',
                'completado': caso.status in ['MDT_COMPLETED', 'REPORT_DRAFT', 'REPORT_COMPLETE', 'CLOSED'],
                'actual': False,
            },
            {
                'titulo': 'Informe Final',
                'descripcion': 'Recibe tu informe de segunda opinión',
                'fecha': caso.updated_at,
                'icono': 'description',
                'completado': caso.status in ['REPORT_COMPLETE', 'OPINION_COMPLETE', 'CLOSED'],
                'actual': caso.status == 'REPORT_COMPLETE',
            },
        ]
    
    context = {
        'caso': caso,
        'opiniones': opiniones,
        'timeline': timeline,
    }
    
    return render(request, 'patients/case_detail_patient.html', context)


@paciente_required
def descargar_informe_caso(request, case_id):
    """Descargar informe final del caso"""
    from cases.models import Case, FinalReport
    
    paciente = request.user
    
    # Buscar primero en Case
    caso = Case.objects.filter(patient=paciente, case_id=case_id).first()
    
    if not caso:
        # Buscar en CasoMDT
        try:
            from cases.mdt_models import CasoMDT
            caso = CasoMDT.objects.filter(paciente=paciente, case_id=case_id).first()
        except:
            caso = None
    
    if not caso:
        raise Http404("Caso no encontrado")
    
    # Buscar informe
    informe = FinalReport.objects.filter(case=caso).first()
    
    if informe and informe.archivo:
        return FileResponse(informe.archivo.open('rb'), as_attachment=True, filename=f'informe_{case_id}.pdf')
    
    messages.info(request, 'La descarga de informes estará disponible pronto.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
