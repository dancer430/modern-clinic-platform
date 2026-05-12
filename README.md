# Medical Booking Platform

A full-stack healthcare scheduling system built with **Django + Vue 3**.
Three roles (**Admin**, **Doctor**, **Patient**) cover the full appointment
lifecycle: book → confirm → complete → cancel, plus doctor schedule
management, medical records, and per-user profile/avatar/password
self-service.

## Quick Start

Prerequisites: `git`, `docker`, `docker compose` v2 (Compose v1 is not
supported). Podman is auto-detected as a fallback.

```bash
cp .env.example .env
# edit .env: set DJANGO_SECRET_KEY, POSTGRES_PASSWORD,
# DJANGO_SUPERUSER_PASSWORD before first boot
# content portal media: MINIO_ROOT_USER, MINIO_ROOT_PASSWORD (see .env.example)
sh ./init-stack.sh
```

The init script auto-detects Podman or Docker, installs Compose v2 if
missing, and brings up all three services.

Force a runtime explicitly:

```bash
sh ./init-stack.sh --runtime=podman   # or --runtime=docker
```

Stale containers / networks blocking startup? Run cleanup, then re-init:

```bash
sh ./cleanup-stack.sh                 # containers + network only
sh ./cleanup-stack.sh --purge-data    # also wipes Postgres volume (irreversible)
```

### Access URLs

- Frontend: http://127.0.0.1:5173
- Backend API: http://127.0.0.1:8000/api/
- Swagger UI: http://127.0.0.1:8000/api/docs/swagger/

### Default Login

The backend bootstrap script creates a Django superuser on first boot from
these `.env` variables (idempotent — safe to leave set):

- `DJANGO_SUPERUSER_USERNAME` (default `admin`)
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

Log in at the frontend with that admin account, then create doctor and
patient accounts from the **Users** page in the admin UI to walk through
the full workflow.

If something goes wrong on first boot, jump to
[`docs/setup.md` → Troubleshooting](docs/setup.md#7-troubleshooting).

## Tech Stack

### Backend
- Python 3.12+
- Django 4.2 + Django REST Framework
- Simple JWT (refresh + blacklist)
- drf-spectacular (OpenAPI / Swagger)
- Database: SQLite for local dev, PostgreSQL in Docker / production
- MinIO (S3-compatible object storage for content portal media)

### Frontend
- Vue 3 + TypeScript
- Vite
- Pinia
- Vue Router
- Axios
- Element Plus (with auto-import)

## Project Layout

```text
modern-clinic-platform/
├── backend/                  # Django API — see backend/README.md
├── frontend/                 # Vue admin console — see frontend/README.md
├── docs/
│   ├── setup.md              # Full setup, validation, and troubleshooting
│   ├── internal/             # Change governance, roadmap, product overview
│   └── superpowers/specs/    # Active refactor program specs
├── openspec/changes/         # OpenSpec change proposals (per-feature)
├── docker-compose.yml        # Default compose stack (db + backend + frontend)
├── docker-compose.2c4g.yml   # Tuned override for 2c4g/50G hosts
├── init-stack.sh             # One-command bring-up (Podman → Docker)
├── cleanup-stack.sh          # Stop containers, optionally purge DB
└── .env.example              # Copy to .env, then edit secrets
```

## Sub-module Docs

- [`backend/README.md`](backend/README.md) — module map, local venv flow,
  pytest/ruff/black, migrations, bootstrap script, OpenAPI regen.
- [`frontend/README.md`](frontend/README.md) — directory map, vitest /
  vue-tsc / build commands, feature-boundary conventions, auto-imports,
  debugging tips.

## Dev Workflow Convention

For every change in this repository:

1. Create a `feature/*` branch from the latest `main`.
2. Implement and verify locally (tests + lint + manual smoke).
3. Commit on the feature branch.
4. Push and open a Pull Request.
5. Merge after CI and review pass.
6. Switch back to local `main` and pull the latest remote.

CI lives at `.github/workflows/ci.yml` and gates merges on
`backend-tests`, `migrations-check`, and `frontend-tests`.

## Further Reading

- [`docs/setup.md`](docs/setup.md) — full setup, env vars, validation,
  Troubleshooting.
- [`docs/internal/`](docs/internal/) — change governance, roadmap,
  product overview. Read before proposing a non-trivial change.
- [`docs/superpowers/specs/2026-04-26-clinic-platform-refactor-design.md`](docs/superpowers/specs/2026-04-26-clinic-platform-refactor-design.md)
  — top-level design for the active full-stack refactor program.
