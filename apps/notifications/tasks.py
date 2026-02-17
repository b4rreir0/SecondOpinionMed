from celery import shared_task
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from .models import EmailLog
import time


RETRY_SCHEDULE = [30, 60, 300, 900, 1800]  # seconds: 30s,1m,5m,15m,30m
MAX_RETRIES = len(RETRY_SCHEDULE)


@shared_task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=60)
def send_email_task(self, email_log_id):
    try:
        email_log = EmailLog.objects.get(id=email_log_id)
    except EmailLog.DoesNotExist:
        return False

    # Render templates
    try:
        context = email_log.context_json or {}
        html_body = render_to_string(email_log.template_name, context)
        plain_body = render_to_string(email_log.template_name.replace('.html', '.txt'), context)
    except Exception:
        # Fallback: use subject as plain message
        html_body = ''
        plain_body = email_log.subject

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

    msg = EmailMultiAlternatives(
        subject=email_log.subject,
        body=plain_body,
        from_email=from_email,
        to=[email_log.recipient],
    )
    if html_body:
        msg.attach_alternative(html_body, 'text/html')

    try:
        # Optionally use explicit connection to control timeouts
        conn = get_connection()
        conn.open()
        msg.send(fail_silently=False)
        email_log.mark_sent()
        return True
    except Exception as exc:
        # Update retries and status
        email_log.mark_retrying(error_message=str(exc))
        retries = email_log.retries_attempted
        if retries >= MAX_RETRIES:
            email_log.mark_failed(error_message=str(exc))
            return False
        # exponential backoff schedule
        delay = RETRY_SCHEDULE[min(retries - 1, len(RETRY_SCHEDULE) - 1)] if retries > 0 else RETRY_SCHEDULE[0]
        try:
            raise self.retry(exc=exc, countdown=delay)
        except Exception:
            # If retry API not available or fails, sleep and try again synchronously
            time.sleep(delay)
            return send_email_task(email_log_id)


# =============================================================================
# TAREAS DE NOTIFICACIÓN MDT
# =============================================================================

@shared_task
def notificar_asignacion_caso(medico_id, caso_id):
    """
    Envía notificación cuando un caso es asignado a un médico.
    """
    from django.contrib.auth import get_user_model
    from .models import Notification
    
    User = get_user_model()
    try:
        medico = User.objects.get(id=medico_id)
        from cases.models import Case
        caso = Case.objects.get(id=caso_id)
        
        Notification.objects.create(
            receptor=medico,
            tipo='asignacion_caso',
            titulo=f"Nuevo caso asignado: {caso.case_id}",
            mensaje=f"Se le ha asignado el caso {caso.case_id} ({caso.specialty_required}).",
            enlace=f'/medicos/casos/{caso.id}/',
            caso_id=caso.case_id
        )
    except Exception as e:
        print(f"Error notifying case assignment: {e}")


@shared_task
def notificar_recordatorio_voto(caso_id):
    """
    Envía recordatorios a médicos que no han votado.
    """
    from .models import Notification
    from cases.models import Case
    
    try:
        caso = Case.objects.get(id=caso_id)
        if not caso.medical_group:
            return
        
        # Obtener médicos que no han votado
        medicos_votaron = caso.opiniones.values_list('doctor_id', flat=True)
        medicos_pendientes = caso.medical_group.miembros.filter(
            activo=True
        ).exclude(medico_id__in=medicos_votaron)
        
        for membresia in medicos_pendientes:
            medico = membresia.medico
            Notification.objects.create(
                receptor=medico.usuario,
                tipo='recordatorio_voto',
                titulo=f"Recordatorio: Caso {caso.case_id}",
                mensaje=f"Aún no ha emitido su opinión sobre el caso {caso.case_id}.",
                enlace=f'/medicos/casos/{caso.id}/opinion/',
                caso_id=caso.case_id
            )
    except Exception as e:
        print(f"Error sending vote reminder: {e}")


@shared_task
def notificar_informe_paciente(caso_id):
    """
    Envía notificación al paciente cuando el informe está listo.
    """
    from .models import Notification
    from cases.models import Case
    
    try:
        caso = Case.objects.get(id=caso_id)
        
        Notification.objects.create(
            receptor=caso.patient,
            tipo='informe_disponible',
            titulo=f"Informe médico disponible - Caso {caso.case_id}",
            mensaje="Su informe médico final ya está disponible para descargar.",
            enlace=f'/pacientes/casos/{caso.id}/',
            caso_id=caso.case_id
        )
    except Exception as e:
        print(f"Error notifying patient: {e}")
