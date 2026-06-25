"""The AccessLog model: an audit trail of PHI access."""
from django.conf import settings
from django.db import models


class AccessLog(models.Model):
    """Records every access to a patient record for HIPAA audit purposes.

    Audit entries must outlive the records they describe, so the foreign keys
    use ``SET_NULL`` and a denormalised ``patient_identifier`` snapshot is kept
    so the trail survives deletion of either the patient or the user.
    """

    class Action(models.TextChoices):
        RETRIEVE = 'RETRIEVE', 'Retrieve'
        INTAKE = 'INTAKE', 'Intake'

    accessed_patient = models.ForeignKey(
        'api.PatientRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_logs',
    )
    # Snapshot of the patient_id that was requested, preserved even if the
    # underlying patient record is later deleted.
    patient_identifier = models.CharField(max_length=64)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_access_logs',
    )
    action = models.CharField(
        max_length=16, choices=Action.choices, default=Action.RETRIEVE
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'api'
        ordering = ['-accessed_at']
        verbose_name = 'access log'
        verbose_name_plural = 'access logs'
        indexes = [
            models.Index(fields=['patient_identifier', 'accessed_at']),
        ]

    def __str__(self):
        who = self.user_id or 'anonymous'
        return f'{self.action} {self.patient_identifier} by {who} @ {self.accessed_at:%Y-%m-%d %H:%M:%S}'
