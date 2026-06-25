"""
This makes ``@shared_task`` work across the project and lets Celery share the
Django configuration.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
