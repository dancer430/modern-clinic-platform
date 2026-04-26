# Harden Settings and Attachments

## Why

Two long-standing risks remain after the service-layer change:

1. **Settings silently misconfigured in production.** `backend/config/settings.py` reads `POSTGRES_*` env vars with default fallbacks (`medcare_prod`, `medcare`, `127.0.0.1`, etc.). When a real production deployment forgets to set `POSTGRES_PASSWORD`, the backend connects to localhost with the literal string "medcare" and fails opaquely — or worse, succeeds against a wrong database. There is no log configuration either: `runserver.log` collects ad-hoc Django output.
2. **Attachments stored as base64 in `TextField`.** `AppointmentAttachment.image_data`, `User.avatar_data`, and `PlatformSetting.logo_data` all keep image bytes inline as base64 strings in the row. The view layer carries a special-case "attachments are only supported when database is PostgreSQL" guard because base64 columns blow past SQLite's row-size limit at scale. Validation only checks `startswith("data:image/")`. There is no enforced size limit at the storage boundary, no real MIME validation, and no path forward to object storage.

This change makes settings explicit-about-failure and moves attachments to real file storage.

## What Changes

This sub-change ships in two safely-orderable parts:

### Part A: Settings hardening (no data migration)

- Validate required env vars at startup in production (`ENV=production`):
  - `DJANGO_SECRET_KEY` must be set and not equal to the dev default.
  - `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_HOST` must be set.
  - `DJANGO_ALLOWED_HOSTS` must be set and non-empty.
  - When any of those is missing, `manage.py` / `gunicorn` startup raises `ImproperlyConfigured` with a list of the missing names.
- Add a structured `LOGGING` block: console handler in dev, JSON-formatted to stdout in prod (suitable for Docker's logging driver).
- Add a sanity-check management command `check_env` that prints which variables are present so deployments can self-test before promoting.

### Part B: Attachment storage migration

- `AppointmentAttachment` gains an `image: ImageField(upload_to="attachments/...")` column; `User.avatar` and `PlatformSetting.logo` likewise gain ImageField columns. The legacy `*_data` TextField columns are kept for one release as read-only fallbacks.
- A reversible data migration (`RunPython`) converts existing rows: decode base64, write to `MEDIA_ROOT`, populate the new field.
- The completion view drops the `connection.vendor != "postgresql"` guard.
- Serializers accept `multipart/form-data` uploads in addition to base64 data URLs (transitional). Clients can keep sending base64 until the next change archives the legacy columns.

## Scope

In scope (Part A):
- env validation
- logging
- `check_env` management command
- pytest assertions that production-env startup raises when required vars missing

In scope (Part B):
- model fields, migrations, serializer surface, file storage backend
- frontend upload code update only if needed; backend compatibility shim accepts both formats

Out of scope:
- moving to object storage (S3/Alauda OSS); the `default_storage` abstraction stays so a future change is a settings-only swap
- Celery/Redis for image compression; client-side compression already happens in the browser
- splitting settings into multiple modules (`base/dev/prod`); this is risky for the current `ENV`-driven init-stack.sh + Dockerfile setup; deferred to a follow-up change
- removing the legacy `*_data` columns (a separate "drop-legacy-attachment-columns" change)

## Expected Outcome

After Part A:
- Starting the backend in production with missing env vars fails at the first request with a clear `ImproperlyConfigured` message listing exactly which vars are missing.
- Logs are JSON-structured and routed to stdout in prod.
- `python manage.py check_env` works locally and in containers.

After Part B:
- New attachments and avatars land in `MEDIA_ROOT` (or whatever `default_storage` points at).
- Existing rows are still readable via the legacy field; reads transparently prefer the new field if present.
- The "attachments require PostgreSQL" runtime branch is gone.
