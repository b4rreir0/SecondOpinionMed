from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from .services import generate_presigned_post
from cases.models import Case, CaseDocument
from documents.tasks import anonymize_document
import logging

log = logging.getLogger(__name__)


@login_required
@require_POST
def get_presigned_upload(request):
    user = request.user
    case_id = request.POST.get('case_id')
    filename = request.POST.get('filename')
    content_type = request.POST.get('content_type', '')
    doc_type = request.POST.get('document_type', 'other')

    case = Case.objects.filter(case_id=case_id).first()
    if not case or not case.is_patient_case(user):
        return HttpResponseForbidden()

    log.info('get_presigned_upload request: user=%s case_id=%s filename=%s', user.email, case_id, filename)
    post, key = generate_presigned_post(case, filename, content_type)

    cd = CaseDocument.objects.create(
        case=case,
        document_type=doc_type,
        s3_file_path=key,
        file_name=filename,
        uploaded_by=user,
    )

    log.info('CaseDocument created id=%s case_id=%s key=%s', cd.id, case.case_id, key)

    # Disparar tarea asíncrona de anonimización; la tarea actualizará el CaseDocument
    anonymize_document.delay(key, cd.id)

    return JsonResponse({'presigned': post, 'document_id': cd.id})
