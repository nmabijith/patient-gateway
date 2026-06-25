# Patient Interoperability Gateway (PIGW)

A small Django/DRF service that ingests patient data from an external EHR system
in FHIR R4 format, stores it with the sensitive bits encrypted, and hands a
sanitized version back to downstream consumers. Built with HIPAA-style handling
of PHI in mind (encryption at rest, SSN masking on read, and an access audit
trail).

## Stack

- Python 3.10+
- Django 6.0 + Django REST Framework
- PostgreSQL
- Redis (JWT storage + Celery broker)
- Celery for the background "welcome email"
- `cryptography` (Fernet) for field-level encryption

## How the project is laid out

I kept the ORM models, background jobs and migrations in their own top-level
packages instead of burying everything inside one app, so each concern is easy
to find:

```
patient_gateway/
├── manage.py
├── requirements.txt
├── .env.example
└── patient_gateway/
    ├── settings.py
    ├── urls.py
    ├── celery.py
    ├── constants.py          # fixed app constants (e.g. minimum age)
    ├── api/                  # the Django app ("api")
    │   ├── apps.py           # points the app's models at ../models
    │   ├── auth/             # login endpoint (JWT)
    │   └── patient/          # intake + retrieval (views, serializers, service layer)
    ├── jobs/                 # Celery tasks, one file per job
    ├── migrations/           # api app migrations live here
    ├── models/              # User, PatientRecord, AccessLog, EncryptedCharField
    └── utilities/            # shared helpers (redis client)
```

A couple of things that look unusual but are deliberate:

- The models sit in `patient_gateway/models/` (a sibling of the app) rather than
  in `api/models.py`. `api/apps.py` overrides `import_models()` to load them, and
  every model sets `app_label = 'api'`. Migrations still belong to the `api` app
  and are stored in `patient_gateway/migrations/` via `MIGRATION_MODULES`.
- Each API area (`auth`, `patient`) is a folder with its own `views.py`,
  `urls.py` and a `*_biz.py` service layer, so the views stay thin and the
  business logic is testable on its own.

## Setup

You'll need Postgres and Redis running locally.

```bash
# 1. virtualenv
python -m venv env
source env/bin/activate          # Windows: env\Scripts\activate

# 2. dependencies
pip install -r requirements.txt

# 3. environment
cp .env.example .env
```

Then fill in `.env`. Most values are fine as-is for local dev, but two need a
real value:

- `DB_PASSWORD` – the password for your Postgres user.
- `FIELD_ENCRYPTION_KEY` – the key used to encrypt PHI. Generate one with:

  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```

Create the database (matching `DB_NAME` / `DB_USER` in your `.env`):

```bash
createdb patient_gateway
# or from psql:
#   CREATE DATABASE patient_gateway;
#   CREATE USER pigw_user WITH PASSWORD '...';
#   GRANT ALL PRIVILEGES ON DATABASE patient_gateway TO pigw_user;
```

Run the migrations and create a user to log in with:

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Running it

```bash
python manage.py runserver
```

By default Celery runs in eager mode (`CELERY_TASK_ALWAYS_EAGER=True`), so the
welcome email runs in-process and prints to the console where `runserver` is
running — no worker needed to try things out. If you want to run it for real,
set that to `False` and start a worker:

```bash
celery -A patient_gateway worker -l info
```

## API

Everything is under `/api/v1/`. The two patient endpoints require a JWT; login
does not.

| Method | Endpoint | Auth | What it does |
|--------|----------|------|--------------|
| POST | `/api/v1/auth/login/` | – | username + password → access/refresh tokens |
| POST | `/api/v1/patients/intake/` | Bearer | ingest a FHIR Patient resource |
| GET | `/api/v1/patients/<patient_id>/` | Bearer | fetch a patient (SSN masked) |

### 1. Log in

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "<your-user>", "password": "<your-password>"}'
```

Response:

```json
{ "access": "<jwt>", "refresh": "<jwt>" }
```

Pass the access token on the protected endpoints as
`Authorization: Bearer <access>`. The issued tokens are also written to Redis
(keyed by user, with a TTL matching the token lifetime).

### 2. Intake

```bash
curl -X POST http://localhost:8000/api/v1/patients/intake/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Patient",
    "id": "example-123",
    "active": true,
    "name": [{"use": "official", "family": "Chalmers", "given": ["Peter", "James"]}],
    "gender": "male",
    "birthDate": "1980-12-25",
    "identifier": [
      {"system": "http://hl7.org/fhir/sid/us-ssn", "value": "000-12-3456"}
    ],
    "telecom": [{"system": "phone", "value": "(555) 555-5555", "use": "home"}]
  }'
```

The endpoint validates the payload, rejects anyone under 18, stores the SSN /
passport encrypted, keeps the original JSON for audit, and kicks off the welcome
email. It returns `201` with the sanitized record (the `patient_id` UUID you use
for retrieval).

Patients younger than 18 are rejected:

```json
{ "birthDate": ["Patient must be at least 18 years old (age: 11)."] }
```

### 3. Retrieve

```bash
curl http://localhost:8000/api/v1/patients/<patient_id>/ \
  -H "Authorization: Bearer <access>"
```

The SSN comes back masked (`***-**-3456`), the passport number isn't returned at
all, and the access is recorded in the audit log.


```

## Design decisions

### Encrypting the SSN (and passport)

The SSN and passport number are stored encrypted using a custom model field,
`EncryptedCharField` (see `patient_gateway/models/fields.py`). It's a `TextField`
subclass that encrypts on the way into the database (`get_prep_value`) and
decrypts on the way out (`from_db_value`), so the rest of the code just works
with plain strings and never deals with ciphertext.

Encryption is done with **Fernet** from the `cryptography` library — that's
AES-128-CBC with an HMAC-SHA256 authentication tag, so tampering with a stored
value is detected on read. A few things worth calling out:

- The key comes from `FIELD_ENCRYPTION_KEY`, kept separate from Django's
  `SECRET_KEY` so it can be rotated and managed on its own (a secrets manager /
  KMS in production).
- The field uses `MultiFernet`, so you can supply comma-separated keys to rotate:
  new writes use the first key, reads try all of them. Re-saving the rows then
  migrates them to the new key.
- Fernet uses a fresh IV each time, so the same SSN encrypts to different
  ciphertext on every write. Good for privacy, but it does mean you can't do an
  exact-match `WHERE ssn = ...` query or put a unique constraint on the column —
  an acceptable trade-off here since we look patients up by their UUID.

I went with a custom field over a third-party "encrypted fields" package on
purpose: it's only a few lines, has no extra dependency to fall behind Django's
release cycle, and it's easy to point at exactly what's happening for a review.

### A couple of other choices

- **Masking on read** lives on the model (`PatientRecord.masked_ssn`) and is
  applied by the output serializer, so the encrypted value never leaves the API
  unmasked. The passport number isn't exposed by the read endpoint at all.
- **Audit log** — every retrieval writes an `AccessLog` row (user, IP, user
  agent, timestamp). The foreign keys are `SET_NULL` and the patient id is also
  stored as a plain string snapshot, so the trail survives even if the patient
  or user record is later deleted.
- **JWT in Redis** — on login the tokens are cached in Redis keyed by user. Right
  now it's mostly a store/tracking mechanism; it also gives us a hook for
  server-side revocation later.
- **Custom user model** from day one, so we never have to do the painful
  `AUTH_USER_MODEL` swap on an existing database.

## If I had more time

- Finish the test scripts.
