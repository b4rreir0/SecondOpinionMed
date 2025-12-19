from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Case


@receiver(post_save, sender=Case)
def assign_case_on_create_or_localidad_change(sender, instance: Case, created, **kwargs):
    """
    Cuando se crea un Case o se actualiza su localidad, si tiene localidad y no tiene
    doctor asignado, intentar asignarlo al medico responsable de la localidad.
    """
    try:
        # If doctor already assigned, nothing to do
        if instance.doctor:
            return

        loc = getattr(instance, 'localidad', None)
        if not loc:
            return

        medico = getattr(loc, 'medico', None)
        if not medico:
            return

        usuario = getattr(medico, 'usuario', None)
        if not usuario:
            return

        # Assign using CaseService to keep auditing and permissions
        try:
            from .services import CaseService
            CaseService.assign_case_to_doctor(instance, usuario)
        except Exception:
            # best-effort: set fields directly as fallback
            instance.doctor = usuario
            instance.status = 'IN_REVIEW'
            instance.assigned_at = timezone.now()
            instance.save()
    except Exception:
        # Swallow exceptions to avoid breaking request flow; logging recommended
        try:
            import logging
            logging.getLogger(__name__).exception('Failed to auto-assign case %s', getattr(instance, 'case_id', instance.pk))
        except Exception:
            pass
