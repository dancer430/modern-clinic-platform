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

Cleanup stale containers/networks before re-deploy:

```bash
sh ./cleanup-stack.sh
```

For full startup and deployment details, see:

- [Setup Guide](docs/setup.md)

## Development Workflow Convention

For this repository, use the following Git workflow for every change:

1. Create a new `feature/*` branch from the latest `main`
2. Implement and verify changes locally
3. Commit on the feature branch
4. Push and open a Pull Request
5. Merge the PR after checks/review pass
6. Switch back to local `main` and pull latest remote updates

This is the default operating convention for ongoing development.

## Change Governance

This repository now uses OpenSpec as the default entry point for all non-trivial changes.

- Micro-changes such as typo fixes, comment edits, and style-only adjustments may skip OpenSpec.
- Any non-trivial change should begin under `openspec/changes/<change-name>/` with:
  - `proposal.md`
  - `design.md`
  - `tasks.md`

Start with:

- [Change Governance Guide](docs/change-governance.md)
- [Change Roadmap](docs/change-roadmap.md)

Current architecture and workflow change chain:

- `openspec/changes/adopt-openspec-change-governance/`
- `openspec/changes/standardize-frontend-feature-boundaries/`
- `openspec/changes/modularize-appointment-page-flow/`
- `openspec/changes/unify-auth-client-responsibilities/`
- `openspec/changes/establish-test-and-ci-baseline/`
- `openspec/changes/introduce-backend-service-layer/`

The active full-stack refactor program is described top-down in
[`docs/superpowers/specs/2026-04-26-clinic-platform-refactor-design.md`](docs/superpowers/specs/2026-04-26-clinic-platform-refactor-design.md).
