# Medical Booking Platform

Medical Booking Platform is a full-stack healthcare scheduling system built with **Django + Vue 3**.
It supports three roles (**Admin**, **Doctor**, **Patient**) and covers core workflows including appointments, scheduling, medical records, and profile management.

## Features

- Multi-role authentication and authorization (Admin / Doctor / Patient)
- End-to-end appointment lifecycle:
  - Create
  - Confirm
  - Complete
  - Cancel
- Doctor schedule management with slot-level availability control
- Medical records view based on completed appointments
- Personal center:
  - Contact/profile update
  - Avatar upload
  - Secure password change
- Server-side pagination for appointment and medical record lists

## Tech Stack

### Backend

- Python 3.12+
- Django 4.2
- Django REST Framework
- Simple JWT (refresh + blacklist)
- drf-spectacular (OpenAPI / Swagger)
- Database strategy:
  - Development: SQLite
  - Production: PostgreSQL

### Frontend

- Vue 3 + TypeScript
- Vite
- Pinia
- Vue Router
- Axios

## Project Structure

```text
booking_demo/
├── backend/          # Django API
├── frontend/         # Vue admin console
├── docs/             # Project documentation
│   └── setup.md      # Setup and deployment guide
└── docker-compose.yml
```

## Quick Start

One-command init (prefer Podman, fallback Docker, auto-install if missing):

```bash
sh ./init-stack.sh
```

Force Podman runtime:

```bash
sh ./init-stack.sh --runtime=podman
```

For full startup and deployment details, see:

- [Setup Guide](docs/setup.md)
