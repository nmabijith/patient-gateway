from django.urls import path

from .views import PatientHealthCheckView

urlpatterns = [
    path('health/', PatientHealthCheckView.as_view(), name='patient-health'),
]
