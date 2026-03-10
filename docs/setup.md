# Setup Guide

This guide provides a one-command startup flow with process guardians for both backend and frontend.

## 1) Recommended: One-Command Startup (Docker Compose)

### 1.1 Prerequisites

- Docker
- Docker Compose v2 (`docker compose`)

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
