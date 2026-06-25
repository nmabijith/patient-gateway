"""Service layer for the patient domain: ingestion, retrieval and audit."""
from django.shortcuts import get_object_or_404

from patient_gateway.models import AccessLog, PatientRecord
from patient_gateway.jobs.welcome_email import send_welcome_email


def ingest_patient(serializer):
    """Persist a validated FHIR patient and trigger post-ingestion side effects.

    `serializer` must be a validated FHIRPatientIntakeSerializer.
    """
    patient = PatientRecord.objects.create(**serializer.to_patient_data())
    send_welcome_email.delay(str(patient.patient_id))
    return patient


def get_patient(patient_id):
    """Return the PatientRecord for the public UUID, or raise Http404."""
    return get_object_or_404(PatientRecord, patient_id=patient_id)


def log_patient_access(patient, request, action=AccessLog.Action.RETRIEVE):
    """Write an audit entry recording who accessed a patient record, from where."""
    user = request.user if request.user.is_authenticated else None
    AccessLog.objects.create(
        accessed_patient=patient,
        patient_identifier=str(patient.patient_id),
        user=user,
        action=action,
        ip_address=_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
    )


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
