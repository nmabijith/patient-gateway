"""Model package.

Models physically live in this package but logically belong to the ``api``
Django app (each declares ``app_label = 'api'``). They are re-exported from
``patient_gateway/api/models.py`` so Django discovers them and creates their
migrations under the ``api`` app. Import them from here for convenience:

    from patient_gateway.models import PatientRecord
"""
from .access_log import AccessLog
from .patient import PatientRecord, mask_ssn
from .user import User

__all__ = ['User', 'PatientRecord', 'AccessLog', 'mask_ssn']
