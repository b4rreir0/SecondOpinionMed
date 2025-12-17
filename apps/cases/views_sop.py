from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import PatientProfileForm, CaseDraftForm, CaseDocumentForm, ReviewConsentForm
from .services import CaseService
from django.conf import settings
import datetime


def _serialize_for_session(value):
    """Recursively convert non-JSON-serializable objects (dates, datetimes)
    to strings for safe storage in the session.
    """
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize_for_session(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_for_session(v) for v in value]
    return value

SESSION_KEY = 'sop_draft'


@login_required
def start_sop(request):
    # Redirect to step 1
    return redirect('cases:sop_step1')


@login_required
def sop_step1(request):
    user = request.user
    initial = {}
    # prefill from existing PatientProfile if present
    try:
        profile = user.patient_profile
        initial = {
            'full_name': profile.full_name,
            'email': user.email,
            'phone': profile.phone_number,
            'medical_history': profile.medical_history,
            'current_medications': profile.current_treatment,
            'known_allergies': '',
        }
    except Exception:
        pass

    if request.method == 'POST':
        form = PatientProfileForm(request.POST)
        if form.is_valid():
            draft = request.session.get(SESSION_KEY, {})
            draft.update({'patient_profile': _serialize_for_session(form.cleaned_data)})
            request.session[SESSION_KEY] = draft
            request.session.modified = True
            return redirect('cases:sop_step2')
    else:
        form = PatientProfileForm(initial=initial)

    return render(request, 'sop/step1_patient.html', {'form': form, 'current_step': 1})


@login_required
def sop_step2(request):
    if request.method == 'POST':
        form = CaseDraftForm(request.POST)
        if form.is_valid():
            draft = request.session.get(SESSION_KEY, {})
            draft.update({'case_draft': _serialize_for_session(form.cleaned_data)})
            request.session[SESSION_KEY] = draft
            request.session.modified = True
            return redirect('cases:sop_step3')
    else:
        draft = request.session.get(SESSION_KEY, {})
        initial = draft.get('case_draft', {})
        form = CaseDraftForm(initial=initial)

    return render(request, 'sop/step2_case.html', {'form': form, 'current_step': 2})


@login_required
def sop_step3(request):
    # we allow multiple uploads by repeating the form
    if request.method == 'POST':
        form = CaseDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # Register metadata in session and rely on presigned upload endpoint
            draft = request.session.get(SESSION_KEY, {})
            docs = draft.get('documents', [])
            f = request.FILES['document']
            # For direct-to-s3 flow we would request a presigned URL; here we store temp metadata
            docs.append({'name': f.name, 'content_type': f.content_type, 'type': form.cleaned_data['document_type']})
            draft['documents'] = docs
            request.session[SESSION_KEY] = draft
            request.session.modified = True
            return redirect('cases:sop_step3')
    else:
        form = CaseDocumentForm()

    draft = request.session.get(SESSION_KEY, {})
    documents = draft.get('documents', [])

    return render(request, 'sop/step3_documents.html', {'form': form, 'documents': documents, 'current_step': 3})


@login_required
def sop_step4(request):
    draft = request.session.get(SESSION_KEY, {})
    if request.method == 'POST':
        form = ReviewConsentForm(request.POST)
        if form.is_valid():
            # Before finalizing, update session draft with any inline edits from the review form
            draft = request.session.get(SESSION_KEY, {})
            # Patient fields
            p = draft.get('patient_profile', {}) or {}
            p.update({
                'full_name': request.POST.get('patient_full_name', p.get('full_name')),
                'age': request.POST.get('patient_age', p.get('age')),
                'email': request.POST.get('patient_email', p.get('email')),
                'phone': request.POST.get('patient_phone', p.get('phone')),
                'medical_history': request.POST.get('patient_medical_history', p.get('medical_history')),
                'current_medications': request.POST.get('patient_current_medications', p.get('current_medications')),
                'known_allergies': request.POST.get('patient_known_allergies', p.get('known_allergies')),
            })
            draft['patient_profile'] = p

            # Case fields
            c = draft.get('case_draft', {}) or {}
            c.update({
                'primary_diagnosis': request.POST.get('case_primary_diagnosis', c.get('primary_diagnosis')),
                'diagnosis_date': request.POST.get('case_diagnosis_date', c.get('diagnosis_date')),
                'referring_institution': request.POST.get('case_referring_institution', c.get('referring_institution')),
                'main_symptoms': request.POST.get('case_main_symptoms', c.get('main_symptoms')),
            })
            draft['case_draft'] = c

            request.session[SESSION_KEY] = draft
            request.session.modified = True

            # finalize: create PatientProfile and Case atomically in service
            explicit = form.cleaned_data.get('explicit_consent', False)
            case = CaseService.finalize_submission(request.user, draft, explicit_consent=explicit)
            # Audit log of creation
            CaseService.log_case_access(case, request.user, action='create')
            # Clean session
            try:
                del request.session[SESSION_KEY]
            except KeyError:
                pass
            # Add a success message and redirect to patient dashboard where created case is visible
            try:
                messages.success(request, f"Solicitud creada: {case.case_id}")
            except Exception:
                pass
            return redirect('cases:patient_dashboard')
    else:
        form = ReviewConsentForm()

    return render(request, 'sop/step4_review.html', {'form': form, 'draft': draft, 'current_step': 4})
