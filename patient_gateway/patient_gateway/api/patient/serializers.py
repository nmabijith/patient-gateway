"""Serializers for the patient API: FHIR intake and sanitized retrieval."""
from django.utils import timezone
from rest_framework import serializers

from patient_gateway.constants import Constants
from patient_gateway.models import PatientRecord

# FHIR R4 identifier systems / codes used to locate PHI in a Patient resource.
SSN_SYSTEM = 'http://hl7.org/fhir/sid/us-ssn'
PASSPORT_TYPE_CODE = 'PPN'


def calculate_age(born, today=None):
    """Age in whole years on `today` (defaults to the current date)."""
    today = today or timezone.localdate()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class FHIRPatientIntakeSerializer(serializers.Serializer):
    """Validates a raw FHIR R4 Patient resource and normalises it for storage.

    Enforces the business rules (resource type must be ``Patient``; the patient
    must be at least ``PATIENT_MINIMUM_AGE``) and extracts the PHI identifiers.
    """

    resourceType = serializers.CharField()
    id = serializers.CharField(required=False, allow_blank=True, default='')
    active = serializers.BooleanField(required=False, default=True)
    name = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    gender = serializers.CharField(required=False, allow_blank=True, default='')
    birthDate = serializers.DateField()
    identifier = serializers.ListField(child=serializers.DictField(), required=False, default=list)

    def validate_resourceType(self, value):
        if value != 'Patient':
            raise serializers.ValidationError('resourceType must be "Patient".')
        return value

    def validate_birthDate(self, value):
        today = timezone.localdate()
        if value > today:
            raise serializers.ValidationError('birthDate cannot be in the future.')
        age = calculate_age(value, today)
        if age < Constants.PATIENT_MINIMUM_AGE:
            raise serializers.ValidationError(
                f'Patient must be at least {Constants.PATIENT_MINIMUM_AGE} years old (age: {age}).'
            )
        return value

    def to_patient_data(self):
        """Build the kwargs dict used to create a PatientRecord.

        Requires ``is_valid()`` to have been called first.
        """
        data = self.validated_data
        family_name, given_names = self._extract_name(data['name'])
        ssn, passport_number = self._extract_identifiers(data['identifier'])
        return {
            'fhir_id': data['id'],
            'family_name': family_name,
            'given_names': given_names,
            'gender': data['gender'],
            'birth_date': data['birthDate'],
            'active': data['active'],
            'ssn': ssn,
            'passport_number': passport_number,
            'raw_payload': self.initial_data,
        }

    @staticmethod
    def _extract_name(names):
        """Return (family_name, given_names) from a FHIR name list, preferring
        the entry marked ``use == 'official'``."""
        if not names:
            return '', ''
        official = next((n for n in names if n.get('use') == 'official'), names[0])
        family = official.get('family', '') or ''
        given = ' '.join(official.get('given', []) or [])
        return family, given

    @staticmethod
    def _extract_identifiers(identifiers):
        """Return (ssn, passport_number) located within a FHIR identifier list."""
        ssn = passport_number = None
        for ident in identifiers:
            value = ident.get('value')
            if not value:
                continue
            system = ident.get('system', '') or ''
            type_codes = {
                coding.get('code')
                for coding in ident.get('type', {}).get('coding', [])
            }
            if system == SSN_SYSTEM:
                ssn = value
            elif 'passport' in system.lower() or PASSPORT_TYPE_CODE in type_codes:
                passport_number = value
        return ssn, passport_number


class PatientDetailSerializer(serializers.ModelSerializer):
    """Sanitized read view of a patient. The SSN is masked and the passport
    number is never exposed."""

    ssn = serializers.SerializerMethodField()

    class Meta:
        model = PatientRecord
        fields = [
            'patient_id',
            'fhir_id',
            'family_name',
            'given_names',
            'full_name',
            'gender',
            'birth_date',
            'active',
            'ssn',
            'created_at',
        ]
        read_only_fields = fields

    def get_ssn(self, obj):
        return obj.masked_ssn
