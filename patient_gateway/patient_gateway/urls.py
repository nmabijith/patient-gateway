"""Root URL configuration for the patient_gateway project.

All API endpoints are versioned under ``/api/v1/``.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('patient_gateway.api.auth.urls')),
    path('api/v1/patients/', include('patient_gateway.api.patient.urls')),
]
