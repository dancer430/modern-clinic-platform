---
name: service-update
description: Roll out the latest code to an already-deployed Medical Booking Platform server over SSH. Use when the user wants to update / 更新 / 升级 / 重新部署 a server that already runs the stack, given its IP plus an SSH password or key. Pushes new code, rebuilds images, restarts, and verifies — preserving the existing .env and all data volumes. For a first install use service-deploy; for a health check use service-status.
---

# service-update

Rolling update of an existing deployment. Preserves the server `.env`
and data volumes (Postgres + MinIO).

## When to use

The server is already deployed and the user wants the latest code live.

## Inputs

- **Server IP** (required), **SSH user** (default `root`), **auth** (key
  path or password), port (default 22)
- Optional `--mode push|clone` (default push); `--repo <url>` for clone

## How to run

```bash
.claude/skills/service-update/scripts/update.sh --host <ip> --key <path>
# dry-run first:
.claude/skills/service-update/scripts/update.sh --host <ip> --key <path> --dry-run
```

## What it does

1. Refuses if the server has no existing deployment (`~/clinic-platform/.env`
   missing) — tells you to use service-deploy.
2. Pushes the latest code, **excluding `.env`** so the server's generated
   secrets are untouched. Data volumes are never removed.
3. Re-runs `sh ./init-stack.sh` (which does `compose up -d --build`):
   rebuilds backend/frontend images and restarts. Backend migrations run
   automatically on container start.
4. Verifies the backend schema + frontend endpoints.

## Safety

- Never regenerates secrets and never touches data volumes.
- If you actually need a clean reinstall with fresh secrets, that's
  service-deploy with `--force` (still volume-preserving).
