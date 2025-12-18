from django.contrib import admin
from django.utils import timezone
from .models import EmailLog, EmailTemplate, DoctorInvitation, PatientVerification
from .services import EmailService


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'subject', 'status', 'retries_attempted', 'sent_at', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'sent_at')


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'template_path', 'created_at')


def send_invitation_emails(modeladmin, request, queryset):
    """Admin action: enqueue invitation emails for selected DoctorInvitation objects."""
    count = 0
    for invite in queryset:
        if not invite.is_used and invite.expires_at >= timezone.now():
            EmailService.create_and_queue_email(
                recipient=invite.invited_email,
                template_name='doctor_invite',
                context={'token': str(invite.token), 'invited_by': invite.invited_by.get_full_name() if invite.invited_by else '' , 'register_url': getattr(__import__('django.conf').conf.settings, 'SITE_ROOT', '') + f"/accounts/register/{invite.token}/"},
                subject='Invitación para unirse como médico'
            )
            count += 1
    modeladmin.message_user(request, f"Encoladas {count} invitaciones para envío.")


@admin.register(DoctorInvitation)
class DoctorInvitationAdmin(admin.ModelAdmin):
    list_display = ('invited_email', 'invited_by', 'expires_at', 'is_used', 'created_at')
    actions = [send_invitation_emails]

    def save_model(self, request, obj, form, change):
        """When created from admin, also enqueue the invitation email automatically."""
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new and not obj.is_used and obj.expires_at >= timezone.now():
            # enqueue email
            EmailService.create_and_queue_email(
                recipient=obj.invited_email,
                template_name='doctor_invite',
                context={'token': str(obj.token), 'invited_by': obj.invited_by.get_full_name() if obj.invited_by else '' , 'register_url': getattr(__import__('django.conf').conf.settings, 'SITE_ROOT', '') + f"/accounts/register/{obj.token}/"},
                subject='Invitación para unirse como médico'
            )


@admin.register(PatientVerification)
class PatientVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'expires_at', 'created_at')
