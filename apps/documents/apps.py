from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documents'
    verbose_name = 'Document Management'

    def ready(self):
        # optional: register auditlog for document-related activity if needed
        try:
            from auditlog.registry import auditlog
            # CaseDocument is defined in cases app; registration done in cases.apps
        except Exception:
            pass
