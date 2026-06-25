"""Project-wide constants.

Fixed, non-secret values referenced across the project, exposed through the
:class:`Constants` class (e.g. ``Constants.PATIENT_MINIMUM_AGE``).

Environment-driven configuration (secrets, database, Celery, email, ...) is
NOT defined here -- it is read directly from the environment in settings.py.
Only true constants belong in this file.
"""


class Constants:
    """Fixed application constants (not environment-driven)."""

    # Minimum age, in years, a patient must meet to be admitted by the intake API.
    PATIENT_MINIMUM_AGE = 18
