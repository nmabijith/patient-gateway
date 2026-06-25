from rest_framework.response import Response
from rest_framework.views import APIView


class PatientHealthCheckView(APIView):
    """Simple health check for patient API connectivity."""

    permission_classes = []

    def get(self, request):
        return Response({'status': 'ok', 'service': 'patient_api'})
