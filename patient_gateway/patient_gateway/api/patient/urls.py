from django.urls import path

from .views import PatientDetailView, PatientIntakeView

urlpatterns = [
    path('intake/', PatientIntakeView.as_view(), name='patient-intake'),
    path('<uuid:patient_id>/', PatientDetailView.as_view(), name='patient-detail'),
]
