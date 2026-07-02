from django.shortcuts import render
from django.contrib.auth.models import Group

from core.decorators import admin_required


@admin_required
def panel_gestion(request):
    """Panel de gestión integral del sistema (ruta activa: /admin-portal/gestion/)."""
    from authentication.models import CustomUser, PatientProfile
    from medicos.models import (
        Medico,
        ComiteMultidisciplinario,
        MedicalGroup,
        TipoCancer,
        Especialidad,
        Localidad,
        DoctorGroupMembership,
    )
    from cases.models import Case as CasoMDT, MedicalOpinion, CaseDocument
    from notifications.models import Notification, DoctorInvitation, EmailLog, EmailTemplate

    stats = {
        'usuarios_total': CustomUser.objects.count(),
        'usuarios_activos': CustomUser.objects.filter(is_active=True).count(),
        'grupos': Group.objects.count(),
        'medicos_total': Medico.objects.count(),
        'medicos_activos': Medico.objects.filter(estado='activo').count(),
        'comites': ComiteMultidisciplinario.objects.count(),
        'grupos_medicos': MedicalGroup.objects.count(),
        'especialidades': Especialidad.objects.count(),
        'tipos_cancer': TipoCancer.objects.count(),
        'localidades': Localidad.objects.count(),
        'membresias': DoctorGroupMembership.objects.count(),
        'pacientes_total': PatientProfile.objects.count(),
        'pacientes_activos': CustomUser.objects.filter(role='patient', is_active=True).count(),
        'casos_total': CasoMDT.objects.count(),
        'casos_pendientes': CasoMDT.objects.filter(
            status__in=['SUBMITTED', 'ASSIGNED', 'PROCESSING', 'MDT_IN_PROGRESS', 'IN_REVIEW']
        ).count(),
        'casos_completados': CasoMDT.objects.filter(
            status__in=['CLOSED', 'OPINION_COMPLETE']
        ).count(),
        'opiniones': MedicalOpinion.objects.count(),
        'documentos': CaseDocument.objects.count(),
        'notificaciones': Notification.objects.count(),
        'invitaciones': DoctorInvitation.objects.count(),
        'emails_enviados': EmailLog.objects.count(),
        'plantillas_email': EmailTemplate.objects.count(),
    }

    recientes = {
        'ultimos_casos': CasoMDT.objects.order_by('-created_at')[:5],
        'ultimos_usuarios': CustomUser.objects.order_by('-date_joined')[:5],
        'ultimas_opiniones': MedicalOpinion.objects.order_by('-fecha_emision')[:5],
    }

    return render(
        request,
        'admin/panel_gestion.html',
        {'stats': stats, 'recientes': recientes},
    )
