---
name: service-deploy
description: Provision the Medical Booking Platform on a fresh remote server over SSH. Use when the user wants to deploy / 部署 / 搭建 / 上线 the whole stack to a server given its IP plus an SSH password or key. Copies code, generates a production .env with strong random secrets, runs init-stack.sh (installs Docker/Podman + brings up db, minio, backend, frontend), and verifies. For updating an existing server use service-update; for a health check use service-status.
---

# service-deploy

One-command remote bring-up of the full platform. Wraps `init-stack.sh`
over SSH.

## When to use

The user gives a target server IP and an SSH **password or key path** and
wants the entire platform stood up there (fresh install).

## Inputs to collect from the user

- **Server IP** (required)
- **SSH user** (default `root`; non-root needs passwordless sudo)
- **Auth**: either a **key path** or a **password** (exactly one)
- Optional: SSH port (default 22), code delivery mode (`push` rsync from
  this checkout — default; or `clone` a git URL with `--repo`)

If the user has not provided the IP or a credential, ask for the missing
piece before running. Never invent an IP or password.

## How to run

From the repo root:

```bash
.claude/skills/service-deploy/scripts/deploy.sh \
  --host <ip> --user root --key <path-to-key>
# or password auth:
.claude/skills/service-deploy/scripts/deploy.sh \
  --host <ip> --password '<pw>'
```

Always **dry-run first** to show the plan without touching the server:

```bash
.claude/skills/service-deploy/scripts/deploy.sh --host <ip> --key <path> --dry-run
```

## What it does

1. Validates inputs, tests SSH, checks sudo.
2. **Re-run guard**: if the server already has `~/clinic-platform/.env`
   or running `booking-*` containers, it refuses and tells you to use
   service-update — unless `--force`. It never wipes data volumes.
3. Delivers code (rsync push by default, excludes `.env`, `node_modules`,
   `.venv`, `db.sqlite3`, `.git`, media).
4. Generates a production `.env` with strong random secrets, injects the
   server IP into `DJANGO_ALLOWED_HOSTS` / `HOST_IP` /
   `MINIO_PUBLIC_ENDPOINT`, and saves the admin password + MinIO creds to
   a local gitignored file `.deploy-credentials/<ip>.env`.
5. Runs `sh ./init-stack.sh` on the server.
6. Verifies `http://<ip>:8000/api/schema/` and `http://<ip>:5173/`, then
   prints access URLs + credentials.

## Safety

- Refuses to overwrite an existing deployment without `--force`.
- Generated secrets live only in the local gitignored creds file — relay
  the admin password to the user but do not paste it into committed files
  or shared channels.
- Contains no teardown / data-wipe path by design.
