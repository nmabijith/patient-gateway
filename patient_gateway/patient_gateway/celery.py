
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patient_gateway.settings')

app = Celery('patient_gateway')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks in each app's `tasks` module, and load the background jobs
# package (patient_gateway/jobs/) which auto-imports every job module.
app.autodiscover_tasks()
app.conf.imports = ('patient_gateway.jobs',)
