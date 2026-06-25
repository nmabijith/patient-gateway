"""Patient API endpoints: secure intake (POST) and sanitized retrieval (GET)."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import patient_biz
from .serializers import FHIRPatientIntakeSerializer, PatientDetailSerializer


class PatientIntakeView(APIView):
    """POST /api/v1/patients/intake/

    Accepts a raw FHIR R4 Patient resource, validates it (including the
    under-18 business rule), stores it with PHI encrypted at rest, and triggers
    the welcome-email background job.
    """

    def post(self, request):
        serializer = FHIRPatientIntakeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = patient_biz.ingest_patient(serializer)
        return Response(
            PatientDetailSerializer(patient).data, status=status.HTTP_201_CREATED
        )


class PatientDetailView(APIView):
    """GET /api/v1/patients/<patient_id>/

    Returns a sanitized view of a patient (SSN masked) and records the access
    in the audit log.
    """

    def get(self, request, patient_id):
        patient = patient_biz.get_patient(patient_id)
        patient_biz.log_patient_access(patient, request)
        return Response(PatientDetailSerializer(patient).data)
