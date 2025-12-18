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
