from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = 'Authentication'
    
    def ready(self):
        try:
            from auditlog.registry import auditlog
            from .models import CustomUser, PatientProfile, DoctorProfile
            auditlog.register(CustomUser)
            auditlog.register(PatientProfile)
            auditlog.register(DoctorProfile)
        except Exception:
            pass
