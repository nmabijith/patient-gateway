from importlib import import_module

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patient_gateway.api'
    label = 'api'

    def import_models(self):
        """Load models from the project-level ``patient_gateway.models`` package.

        The models live in ``patient_gateway/models/`` (a sibling of this app)
        rather than in an ``api/models.py`` module. We point the app's models
        module there so Django discovers and registers them under this app --
        each model declares ``app_label = 'api'``. Migrations still live in
        ``patient_gateway/api/migrations/`` (derived from the app name).
        """
        super().import_models()
        self.models_module = import_module('patient_gateway.models')
