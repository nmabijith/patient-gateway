"""Welcome-email background job, run after a patient is ingested."""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail

from patient_gateway.models import PatientRecord

logger = get_task_logger(__name__)


@shared_task
def send_welcome_email(patient_id):
    """Send a welcome email to a newly ingested patient.

    Simulated post-ingestion side effect. The recipient address is read from the
    patient's FHIR ``telecom`` entries; if none is present there is nobody to
    email and the task is a no-op.
    """
    patient = PatientRecord.objects.filter(patient_id=patient_id).first()
    if patient is None:
        logger.warning('send_welcome_email: patient %s not found', patient_id)
        return

    email = _patient_email(patient.raw_payload)
    if not email:
        logger.info('send_welcome_email: no email on file for patient %s', patient_id)
        return

    send_mail(
        subject='Welcome to the Patient Interoperability Gateway',
        message=f'Hello {patient.full_name or "patient"}, your record has been received.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    logger.info('send_welcome_email: welcome email sent to patient %s', patient_id)


def _patient_email(raw_payload):
    for telecom in (raw_payload or {}).get('telecom', []):
        if telecom.get('system') == 'email' and telecom.get('value'):
            return telecom['value']
    return None
