# Setup Guide

This guide provides a one-command startup flow with process guardians for both backend and frontend.

## 1) Recommended: One-Command Startup (Docker Compose)

### 1.1 Prerequisites

- Docker
- Docker Compose v2 (`docker compose`)

Legacy `docker-compose` v1 (for example 1.29.x) is not supported and can fail with errors like `KeyError: 'ContainerConfig'`.

### 1.2 Quick Start

From project root:

```bash
cp .env.example .env
docker compose up -d --build
```

One-command auto init (prefer Podman, fallback Docker, auto install if missing):

```bash
sh ./init-stack.sh
```

If container names/networks conflict or stale resources block startup, run cleanup first:

```bash
sh ./cleanup-stack.sh
```

To also remove PostgreSQL persistent data (irreversible):

```bash
sh ./cleanup-stack.sh --purge-data
```

Force Podman runtime:

```bash
sh ./init-stack.sh --runtime=podman
```

For a 2c4g/50G single-server setup, use the tuned override:

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.2c4g.yml up -d --build
```

What this does:

- Starts PostgreSQL (`db`)
- Starts Django backend (`backend`)
- Runs automatic bootstrap on backend:
  - waits for DB
  - runs migrations
  - auto-creates superuser from env (idempotent)
  - starts `gunicorn`
- Starts frontend (`frontend`) with Nginx serving built assets

All services use daemon/guardian behavior via:

- `restart: unless-stopped`

### 1.3 Access URLs

- Frontend: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:8000/api/`
- Swagger: `http://127.0.0.1:8000/api/docs/swagger/`

### 1.4 Useful Commands

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose down
```

## 2) Environment Variables

Main env file (root): `.env`

Key fields:

- `ENV=production`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=0`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`
- `APT_MIRROR` (optional, default `mirrors.tuna.tsinghua.edu.cn`)
- `PIP_INDEX_URL` (optional, default `https://pypi.tuna.tsinghua.edu.cn/simple`)
- `PIP_TRUSTED_HOST` (optional, default `pypi.tuna.tsinghua.edu.cn`)

Superuser is created automatically on container bootstrap if all 3 superuser env vars are provided.

## 3) Local (Non-Docker) Development

If you still prefer local processes:

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 4) Validation Commands

```bash
cd backend
python manage.py check
python manage.py test

cd frontend
npm run build
```

### 4.1) Tests

The repository ships an automated test and lint baseline. Run it locally before opening a PR; CI runs the same suites on every push.

Backend (pytest + ruff + black):

```bash
cd backend
pip install -r requirements-dev.txt    # one-time, pins pytest, factory_boy, ruff, black
pytest                                  # ≈ 3s, 33 tests today
ruff check .
black --check .
```

Frontend (vitest + vue-tsc):

```bash
cd frontend
npm install
npm run test           # watch mode
npm run test:run       # one-shot, used by CI
npm run typecheck      # vue-tsc -b --noEmit
npm run build          # vue-tsc + vite build
```

CI workflow lives at `.github/workflows/ci.yml` and runs three jobs in parallel: `backend-tests`, `migrations-check`, `frontend-tests`. A merge to `main` is blocked when any job fails.

## 5) Core API Endpoints

### Auth and Profile

- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`
- `PATCH /api/auth/me/`
- `POST /api/auth/change-password/`

### User Management

- `GET/POST/PATCH/DELETE /api/auth/doctors/`
- `GET/POST/PATCH/DELETE /api/auth/patients/`

### Appointments and Records

- `GET/POST /api/appointments/`
- `PUT /api/appointments/{id}/confirm/`
- `PUT /api/appointments/{id}/complete/`
- `PUT /api/appointments/{id}/cancel/`

List supports filters + pagination:

- `status`
- `doctor`
- `patient`
- `date`
- `date_from`
- `date_to`
- `q`
- `page`
- `page_size` (`10/20/50`)

### Schedule

- `GET/POST/PATCH/DELETE /api/schedule-slots/`

## 6) Storage Notes

- Avatar: base64 image data stored in DB (works in SQLite and PostgreSQL)
- Completion attachments:
  - UI supports upload and compression
  - backend persists only when DB is PostgreSQL

## 7) Troubleshooting

The 10 most common first-boot issues, in roughly the order new hires hit
them.

### 7.1 Port 8000 or 5173 already in use

Symptom: `init-stack.sh` fails with `bind: address already in use`, or
the frontend / API URL never responds.

```bash
lsof -i :8000   # find the process holding the port
lsof -i :5173
# either stop the conflicting process, or change the host-side port
# in docker-compose.yml (the "8000:8000" / "5173:80" mapping)
```

### 7.2 `docker-compose` v1 fails with `KeyError: 'ContainerConfig'`

Compose v1 is unsupported. Confirm you have v2:

```bash
docker compose version   # must print "Docker Compose version v2.x.x"
```

If only `docker-compose` (v1) is installed, install Docker Desktop or
the `docker-compose-plugin` package and use `docker compose` (no
hyphen).

### 7.3 Container name conflict

Symptom: `Conflict. The container name "/booking-db"` (or
`booking-backend` / `booking-frontend`) `is already in use`.

```bash
sh ./cleanup-stack.sh
sh ./init-stack.sh
```

### 7.4 Admin login fails after first boot

The bootstrap script will re-sync the superuser's email, role flags,
and password from `.env` on every container start. So the usual fix is
to set the right values in `.env` and restart the backend container:

```bash
docker compose restart backend
docker compose logs -f backend   # watch for "[bootstrap] superuser already exists"
```

If you'd rather change the password directly:

```bash
docker compose exec backend python manage.py changepassword <username>
```

### 7.5 Frontend 5173 blank or 502 from nginx

```bash
docker compose ps                 # confirm "frontend" is "Up"
docker compose logs -f frontend   # nginx error logs surface here
docker compose up -d --build frontend
```

A blank page with the API still working usually means the Vue build
failed silently in a previous run; force a clean build with
`--no-cache` (see 7.8).

### 7.6 Reset the database

```bash
sh ./cleanup-stack.sh --purge-data   # irreversible: drops the postgres volume
sh ./init-stack.sh
```

### 7.7 Migration failure on bootstrap

```bash
docker compose logs -f backend       # find the failing migration
# fix the model or migration in your local checkout, then:
docker compose exec backend python manage.py migrate
```

If the failure is in a migration that already partially ran, prefer
`--fake` or rolling back to the last known-good migration over
hand-editing `django_migrations`.

### 7.8 Frontend `npm run build` fails inside the image

```bash
docker compose build --no-cache frontend
```

If the host-side cache is the suspect (rare, only when you've also
been doing local `npm install`), wipe it locally:

```bash
rm -rf frontend/node_modules frontend/package-lock.json
cd frontend && npm install
```

### 7.9 Switching between Podman and Docker

`init-stack.sh` auto-detects: Podman first, then Docker, with
auto-install on Linux. Force a runtime when both are present:

```bash
sh ./init-stack.sh --runtime=podman
sh ./init-stack.sh --runtime=docker
```

`cleanup-stack.sh` follows the same detection logic — no flag needed.

### 7.10 Internal Alauda mirror unreachable (off-network)

The Dockerfiles pin `docker-mirrors.alauda.cn/library/...` so that
in-network builds skip Docker Hub rate limits. If you are off-network
(e.g. WFH on personal Wi-Fi) the build will hang or fail with a DNS or
TLS error.

Local-only workaround — replace three image references with their
Docker Hub equivalents, then rebuild. **Do not commit this change**;
it is for your local environment only.

```bash
# in backend/Dockerfile
#   FROM docker-mirrors.alauda.cn/library/python:3.12-slim
# →
#   FROM docker.io/library/python:3.12-slim

# in frontend/Dockerfile  (two lines)
#   FROM docker-mirrors.alauda.cn/library/node:20-alpine AS build
#   FROM docker-mirrors.alauda.cn/library/nginx:1.27-alpine
# →
#   FROM docker.io/library/node:20-alpine AS build
#   FROM docker.io/library/nginx:1.27-alpine

# in docker-compose.yml  (db service)
#   image: docker-mirrors.alauda.cn/library/postgres:16-alpine
# →
#   image: docker.io/library/postgres:16-alpine

docker compose build --no-cache
sh ./init-stack.sh
```
