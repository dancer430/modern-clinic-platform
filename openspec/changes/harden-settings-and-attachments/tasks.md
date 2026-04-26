# Tasks

## Part A: Settings hardening (implemented now)

- [x] Add a `REQUIRED_PROD_ENV` tuple in `backend/config/settings.py`
- [x] Raise `ImproperlyConfigured` when `ENV=production` and any required var is missing
- [x] Reject the dev-default `DJANGO_SECRET_KEY` in production
- [x] Add a `LOGGING` block (console formatter in dev, JSON-to-stdout in prod) and `common/logging.py:JsonFormatter`
- [x] Add a `users/management/commands/check_env.py` Django management command
- [x] Add `tests/common/test_settings_validation.py` covering the validation paths
- [x] Add `tests/common/test_logging_format.py` covering the JSON formatter output

## Part B: Attachment storage migration (NOT implemented in this commit)

The model + migration changes touch the database schema and require a careful staging rollout. Per the program's safety policy ("auto mode is not a license to destroy"), this part is left for a follow-up session where the user can drive the migration on a real database.

- [ ] Add `image: ImageField(upload_to="attachments/%Y/%m/%d/", null=True, blank=True)` to `AppointmentAttachment`
- [ ] Add `avatar: ImageField(...)` to `User` (alongside legacy `avatar_data`)
- [ ] Add `logo: ImageField(...)` to `PlatformSetting`
- [ ] Generate the matching `0002_*.py` migrations
- [ ] Write a reversible `RunPython` data migration converting existing base64 rows to files
- [ ] Update `AppointmentAttachmentSerializer` to expose `image_url` and accept either base64 input or multipart upload
- [ ] Drop the `connection.vendor != "postgresql"` guard in `AppointmentViewSet.complete`
- [ ] Add `MEDIA_ROOT` and `MEDIA_URL` settings; add a docker-compose volume for `media_data`
- [ ] Add `tests/appointments/test_attachment_storage.py` covering upload + legacy fallback

## Verification (Part A)

- [x] `pytest` green
- [x] `ruff check . && black --check .` green
- [x] `python manage.py check_env` exits 0 in dev (where the prod requirements are intentionally relaxed); the same command in production with missing env vars exits 1
