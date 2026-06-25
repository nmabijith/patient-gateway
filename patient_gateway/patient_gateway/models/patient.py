"""The PatientRecord model: HIPAA-aware storage for ingested FHIR patients."""
import re
import uuid

from django.db import models

from .fields import EncryptedCharField


def mask_ssn(value):

    if not value:
        return value
    digits = re.sub(r'\D', '', value)
    last4 = digits[-4:]
    return f'***-**-{last4}'


class PatientRecord(models.Model):


    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    ]


    patient_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )

    fhir_id = models.CharField(max_length=255, blank=True)

    family_name = models.CharField(max_length=255, blank=True)
    given_names = models.CharField(max_length=255, blank=True)
    gender = models.CharField(max_length=16, choices=GENDER_CHOICES, blank=True)
    birth_date = models.DateField()
    active = models.BooleanField(default=True)

    ssn = EncryptedCharField(null=True, blank=True)
    passport_number = EncryptedCharField(null=True, blank=True)

    raw_payload = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'api'
        ordering = ['-created_at']
        verbose_name = 'patient record'
        verbose_name_plural = 'patient records'

    def __str__(self):
        return f'PatientRecord({self.patient_id})'

    @property
    def full_name(self):
        return f'{self.given_names} {self.family_name}'.strip()

    @property
    def masked_ssn(self):
        """The SSN with all but the last four digits masked, for safe display."""
        return mask_ssn(self.ssn)
