import uuid
import boto3
import logging
from django.conf import settings

log = logging.getLogger(__name__)


def generate_presigned_post(case, filename, content_type='', expires_in=3600):
    """Genera un presigned POST para subida directa a S3 y devuelve (post_data, key).

    Requiere que las credenciales AWS estén definidas en `settings`.
    """
    log.info('generate_presigned_post start: case_id=%s filename=%s', getattr(case, 'case_id', None), filename)
    s3 = boto3.client(
        's3',
        aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
        aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
        region_name=getattr(settings, 'AWS_REGION', None),
    )

    # Use deterministic per-case folder: cases/{case_id}/{filename}
    # To avoid collisions, prefix with a short uuid
    unique_prefix = uuid.uuid4().hex[:8]
    key = f"cases/{case.case_id}/{unique_prefix}_{filename}"

    fields = {}
    if content_type:
        fields['Content-Type'] = content_type

    post = s3.generate_presigned_post(
        Bucket=getattr(settings, 'AWS_S3_BUCKET_NAME'),
        Key=key,
        Fields=fields,
        Conditions=[],
        ExpiresIn=expires_in,
    )
    log.info('generate_presigned_post end: case_id=%s key=%s', getattr(case, 'case_id', None), key)
    return post, key


def schedule_delete_case_files(case_id, delay_seconds: int = 0):
    """Schedule asynchronous deletion of all case files. Uses Celery task if available.

    This function only enqueues the task; deletion behavior should be gated by
    configuration (see settings.AUTO_DELETE_CASE_FILES).
    """
    log.info('schedule_delete_case_files requested for case_id=%s delay=%s', case_id, delay_seconds)
    try:
        from .tasks import delete_case_files_task
        if delay_seconds and hasattr(delete_case_files_task, 'apply_async'):
            delete_case_files_task.apply_async((case_id,), countdown=delay_seconds)
        else:
            delete_case_files_task.delay(case_id)
        log.info('delete_case_files_task enqueued for case_id=%s', case_id)
    except Exception as e:
        log.exception('Failed to enqueue delete_case_files_task for case_id=%s: %s', case_id, e)
