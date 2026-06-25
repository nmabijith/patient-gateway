"""Background jobs (Celery tasks), grouped in one package.

Every submodule here is imported automatically so its ``@shared_task``
definitions register with Celery. To add a new background job, just drop a new
module in this package -- no wiring required.
"""
import importlib
import pkgutil

for _module in pkgutil.iter_modules(__path__):
    importlib.import_module(f'{__name__}.{_module.name}')
