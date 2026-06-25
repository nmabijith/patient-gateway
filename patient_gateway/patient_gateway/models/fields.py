"""Custom model fields providing transparent field-level encryption.

PHI such as a patient's SSN or passport number must never be stored in the
clear. :class:`EncryptedCharField` encrypts values on their way into the
database and decrypts them transparently on the way out, so the rest of the
application works with plain Python strings and never has to handle ciphertext.

Encryption uses Fernet (AES-128 in CBC mode with an HMAC-SHA256 authentication
tag) from the ``cryptography`` library. Fernet is authenticated, so any
tampering with the stored ciphertext is detected on read. Each encryption uses
a fresh IV, so the same plaintext yields different ciphertext every time --
good for privacy, but it also means encrypted columns cannot be used for
exact-match lookups or unique constraints at the database level.

Key management
--------------
Key(s) are read from ``settings.FIELD_ENCRYPTION_KEY``. To support zero
downtime key rotation, multiple keys may be supplied as a comma-separated list:
new values are always encrypted with the first key, while decryption is
attempted against every key in order. After rotating, re-save existing rows to
migrate their ciphertext to the new key, then retire the old one.
"""
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


@lru_cache(maxsize=1)
def _get_cipher():
    """Build (and cache) the MultiFernet cipher from the configured key(s)."""
    raw = settings.FIELD_ENCRYPTION_KEY
    if not raw:
        raise ImproperlyConfigured(
            'FIELD_ENCRYPTION_KEY is not set. Generate one with: '
            'python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
    keys = [key.strip() for key in raw.split(',') if key.strip()]
    try:
        return MultiFernet([Fernet(key.encode()) for key in keys])
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured(
            'FIELD_ENCRYPTION_KEY is not a valid Fernet key (expected a '
            'url-safe base64-encoded 32-byte key).'
        ) from exc


class EncryptedCharField(models.TextField):
    """A text field whose value is encrypted at rest with Fernet.

    The value is exposed to application code as a normal ``str`` and stored in
    the database as a Fernet token. ``TextField`` is used as the storage base
    because ciphertext is longer than the plaintext and has no meaningful
    ``max_length``.
    """

    description = 'A string stored encrypted at rest using Fernet'

    def from_db_value(self, value, expression, connection):
        """Decrypt the stored token when loading from the database."""
        if value is None:
            return None
        try:
            return _get_cipher().decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise InvalidToken(
                'Unable to decrypt an encrypted field. The value may have been '
                'written with a different FIELD_ENCRYPTION_KEY.'
            ) from exc

    def get_prep_value(self, value):
        """Encrypt the value on its way into the database."""
        value = super().get_prep_value(value)
        if value is None:
            return None
        return _get_cipher().encrypt(value.encode()).decode()
