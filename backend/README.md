# Backend (Django API)

Django 4.2 + DRF service for the Medical Booking Platform. Owns the
domain model (users, appointments, schedule slots, medical records),
JWT authentication, role-based authorization, and the OpenAPI schema
served at `/api/docs/swagger/`.

The Docker path is the recommended way to run the full stack — see the
root [`README.md`](../README.md) for the one-command bring-up. This
document covers the **local non-Docker** workflow and the day-to-day
operations on the backend codebase.

## Module Map

| Path | Responsibility |
|------|---|
| `config/` | Django project settings, root URL conf, ASGI/WSGI entry points. `settings.py` contains the `REQUIRED_PROD_ENV` list used by `check_env`. |
| `users/` | Custom `User` model (with `Role`), authentication views, profile / password / avatar endpoints, doctor & patient management, plus the `check_env` management command under `users/management/commands/`. |
| `appointments/` | Appointment model, schedule slots, status state machine (`pending → confirmed → completed`/`cancelled`), service layer, list filtering, and pagination. |
| `common/` | Cross-cutting infrastructure: uniform error envelope (`errors.py`) and structured logging helpers (`logging.py`). |
| `content/` | Public-facing department and doctor introductions with draft → admin-review → publish workflow; MinIO-backed rich text media; sitemap. |
| `tests/` | Pytest suites mirroring the apps (`tests/users/`, `tests/appointments/`, `tests/common/`), plus shared `factories.py` and `conftest.py`. |
| `scripts/` | Container entry-point scripts. `bootstrap-backend.sh` waits for the DB, runs migrations, syncs the superuser from env, and starts gunicorn. |
| `schema.yaml` | Last regenerated OpenAPI schema. Source of truth for the Swagger UI. |
| `requirements.txt` | Runtime deps. Pinned. |
| `requirements-dev.txt` | Adds pytest, factory_boy, ruff, black. |

## Local Dev (venv + SQLite)

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

cp ../.env.example .env             # then edit DJANGO_SECRET_KEY etc.
python manage.py migrate
python manage.py createsuperuser    # interactive
python manage.py runserver          # http://127.0.0.1:8000/
```

In local dev mode SQLite is used by default (`db.sqlite3`). Attachment
upload is **disabled** outside PostgreSQL by a backend guard (see the
appointments service layer).

## Docker Dev

The full stack runs from the repository root with `sh ./init-stack.sh`.
The backend container mounts `./backend` into `/app`, so editing source
on the host hot-reloads inside the container after a `docker compose
restart backend`. See root [`README.md`](../README.md) and
[`docs/setup.md`](../docs/setup.md).

## Tests, Lint, Format

| Command | Purpose |
|---|---|
| `pytest` | Run the full suite (~3 s, 33 tests as of writing). |
| `pytest -k <pattern>` | Focused run by node id / name pattern. |
| `pytest --cov` | Coverage report (uses `pytest-cov`). |
| `ruff check .` | Lint. |
| `ruff check . --fix` | Lint with safe auto-fixes applied. |
| `black --check .` | Format check (used in CI). |
| `black .` | Apply formatting. |

CI runs `pytest`, `ruff check .`, `black --check .` plus a migrations
parity check. See `.github/workflows/ci.yml`.

## Migrations

```bash
python manage.py makemigrations <app>      # write a new migration
python manage.py migrate                   # apply
python manage.py showmigrations            # list applied / pending
python manage.py sqlmigrate <app> <name>   # inspect generated SQL
```

The migrations-check CI job runs `makemigrations --check --dry-run` and
fails the build if a model change has no matching migration committed.

## Bootstrap Script

`scripts/bootstrap-backend.sh` is the container's `command:`. It:

1. Polls Postgres on `POSTGRES_HOST:POSTGRES_PORT` for up to 60 seconds.
2. Runs `manage.py migrate --noinput`.
3. If `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, and
   `DJANGO_SUPERUSER_PASSWORD` are all set: creates the superuser, or
   re-syncs an existing user's email, role, staff/superuser flags, and
   password to match the env. **This means changing
   `DJANGO_SUPERUSER_PASSWORD` and restarting backend is a valid
   password-reset flow.**
4. Starts gunicorn with `GUNICORN_WORKERS`, `GUNICORN_TIMEOUT`,
   `GUNICORN_MAX_REQUESTS`, `GUNICORN_MAX_REQUESTS_JITTER` (defaults
   tuned for 2c4g).

## OpenAPI Schema

```bash
python manage.py spectacular --file schema.yaml   # regenerate on disk
# Swagger UI:  http://127.0.0.1:8000/api/docs/swagger/
# Raw schema:  http://127.0.0.1:8000/api/schema/
```

Regenerate `schema.yaml` after any DRF view, serializer, or URL change
that affects the public API and commit it together with the change.

## Env-Var Health Check

```bash
python manage.py check_env
```

Prints each variable in `config.settings.REQUIRED_PROD_ENV` as `set` or
`MISSING` and exits non-zero if any are missing. Useful to wire into
container start scripts so deploys fail fast instead of booting with
half-configured env.

## Debugging

- **Backend logs**: `docker compose logs -f backend` — bootstrap output,
  migration progress, gunicorn access logs.
- **Django shell**: `docker compose exec backend python manage.py shell`
  for ad-hoc ORM queries.
- **DB shell**:
  `docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"`
  (env vars come from the running container, so this Just Works after
  `init-stack.sh`).
