from celery import shared_task
import boto3
import tempfile
import os
from django.conf import settings
from cases.models import CaseDocument
import pydicom
import logging
from django.apps import apps as django_apps

log = logging.getLogger(__name__)


@shared_task
def anonymize_document(s3_key, case_document_id):
    """Tarea para descargar un archivo desde S3, intentar anonimizar (DICOM)
    y subir la versión anonimada. Actualiza `CaseDocument.is_anonymized` y `s3_file_path`.
    """
    s3 = boto3.client(
        's3',
        aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
        aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
        region_name=getattr(settings, 'AWS_REGION', None),
    )
    bucket = getattr(settings, 'AWS_S3_BUCKET_NAME')

    tmp_in = tempfile.NamedTemporaryFile(delete=False)
    tmp_out = tempfile.NamedTemporaryFile(delete=False)
    tmp_in.close()
    tmp_out.close()

    try:
        s3.download_file(bucket, s3_key, tmp_in.name)

        try:
            ds = pydicom.dcmread(tmp_in.name)
            # Remove common identifying tags
            for tag in ['PatientName', 'PatientID', 'PatientBirthDate', 'PatientBirthTime', 'PatientAddress']:
                if hasattr(ds, tag):
                    setattr(ds, tag, '')
            ds.remove_private_tags()
            ds.save_as(tmp_out.name)

            # Upload anonymized file to a segregated path
            anon_key = f"anonymized/{s3_key}"
            s3.upload_file(tmp_out.name, bucket, anon_key)

            cd = CaseDocument.objects.filter(id=case_document_id).first()
            if cd:
                cd.s3_file_path = anon_key
                cd.is_anonymized = True
                cd.save()

        except Exception:
            # If file isn't DICOM or anonymization failed, mark as processed=False
            cd = CaseDocument.objects.filter(id=case_document_id).first()
            if cd:
                cd.is_anonymized = False
                cd.save()

    finally:
        try:
            os.unlink(tmp_in.name)
        except Exception:
            pass
        try:
            os.unlink(tmp_out.name)
        except Exception:
            pass


@shared_task
def delete_case_files_task(case_id):
    """Elimina todos los objetos en S3 asociados a un case_id y borra registros CaseDocument.

    Safety: Solo procede si el Case existe y su estado es CLOSED o OPINION_COMPLETE (configurable).
    """
    try:
        Case = django_apps.get_model('cases', 'Case')
        CaseDocument = django_apps.get_model('cases', 'CaseDocument')
        case = Case.objects.filter(case_id=case_id).first()
        if not case:
            log.warning('delete_case_files_task: case not found %s', case_id)
            return

        # Allowed states for deletion
        allowed = getattr(settings, 'CASE_FILE_DELETION_ALLOWED_STATES', ['CLOSED'])
        if case.status not in allowed:
            log.warning('delete_case_files_task: case %s status %s not in allowed %s', case_id, case.status, allowed)
            return

        docs = CaseDocument.objects.filter(case=case)
        if not docs.exists():
            log.info('delete_case_files_task: no documents for case %s', case_id)
            return

        s3 = boto3.client(
            's3',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            region_name=getattr(settings, 'AWS_REGION', None),
        )
        bucket = getattr(settings, 'AWS_S3_BUCKET_NAME', None)
        if not bucket:
            log.error('delete_case_files_task: AWS_S3_BUCKET_NAME not set')
            return

        for cd in docs:
            key = cd.s3_file_path
            if not key:
                log.warning('delete_case_files_task: CaseDocument id=%s has no s3_file_path', cd.id)
                continue
            try:
                s3.delete_object(Bucket=bucket, Key=key)
                log.info('delete_case_files_task: deleted s3 object %s', key)
            except Exception as e:
                log.exception('delete_case_files_task: error deleting %s: %s', key, e)
            try:
                cd.delete()
                log.info('delete_case_files_task: deleted CaseDocument id=%s', cd.id)
            except Exception as e:
                log.exception('delete_case_files_task: error deleting CaseDocument id=%s: %s', cd.id, e)

        log.info('delete_case_files_task: finished for case %s', case_id)
    except Exception:
        log.exception('delete_case_files_task: unexpected error for case %s', case_id)
