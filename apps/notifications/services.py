from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import EmailLog, EmailTemplate, DoctorInvitation
from datetime import timedelta
from .tasks import send_email_task


class EmailService:
    @staticmethod
    def create_and_queue_email(recipient, template_name, context=None, subject=None, from_email=None):
        """Render template, create EmailLog and enqueue Celery task."""
        context = context or {}
        # Try to find template metadata
        template_meta = None
        try:
            template_meta = EmailTemplate.objects.filter(name=template_name).first()
        except Exception:
            template_meta = None

        template_path = template_meta.template_path if template_meta else template_name
        subject = subject or (template_meta.subject if template_meta else 'Notification')
        from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', None)

        # Create EmailLog
        email_log = EmailLog.objects.create(
            recipient=recipient,
            subject=subject,
            template_name=template_path,
            context_json=context,
            status=EmailLog.STATUS_PENDING,
        )

        # Enqueue Celery task
        try:
            send_email_task.delay(email_log.id)
        except Exception:
            # If Celery not available, try synchronous send as fallback
            from .tasks import send_email_task as send_sync
            send_sync(email_log.id)

        return email_log

    @staticmethod
    def invite_doctor(invited_email, invited_by_user):
        expires = timezone.now() + timedelta(hours=72)
        invite = DoctorInvitation.objects.create(
            invited_email=invited_email,
            invited_by=invited_by_user,
            expires_at=expires,
        )

        # Build registration URL
        register_url = f"{getattr(settings, 'SITE_ROOT', '')}/accounts/register/{invite.token}/"

        context = {
            'token': str(invite.token),
            'invited_by': invited_by_user.get_full_name() if hasattr(invited_by_user, 'get_full_name') else str(invited_by_user),
            'register_url': register_url,
        }

        # Queue email using template 'doctor_invite'
        EmailService.create_and_queue_email(
            recipient=invited_email,
            template_name='doctor_invite',
            context=context,
            subject='Invitación para unirse como médico',
        )

        return invite
