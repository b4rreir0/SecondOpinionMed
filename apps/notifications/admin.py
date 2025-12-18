from django.contrib import admin
from .models import EmailLog, EmailTemplate, DoctorInvitation, PatientVerification


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'subject', 'status', 'retries_attempted', 'sent_at', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'sent_at')


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'template_path', 'created_at')


@admin.register(DoctorInvitation)
class DoctorInvitationAdmin(admin.ModelAdmin):
    list_display = ('invited_email', 'invited_by', 'expires_at', 'is_used', 'created_at')


@admin.register(PatientVerification)
class PatientVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'expires_at', 'created_at')
