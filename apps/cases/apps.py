from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cases'
    verbose_name = 'Gestión de Casos'
    
    def ready(self):
        # Register audit logging for critical models if auditlog is available
        try:
            from auditlog.registry import auditlog
            from .models import Case, CaseDocument, SecondOpinion
            auditlog.register(Case)
            auditlog.register(CaseDocument)
            auditlog.register(SecondOpinion)
        except Exception:
            # auditlog not installed or registration failed; skip in dev
            pass
        # Ensure signals are imported so they are registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
