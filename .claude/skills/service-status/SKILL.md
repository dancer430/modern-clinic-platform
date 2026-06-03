---
name: service-status
description: Read-only health check of a deployed Medical Booking Platform server over SSH. Use when the user wants to check status / 状态 / 健康 / 巡检 of a server given its IP plus an SSH password or key. Reports container health (db, minio, backend, frontend) and endpoint reachability. No side effects. For first install use service-deploy; to update use service-update.
---

# service-status

Read-only remote health check. Makes no changes.

## When to use

The user wants to know whether a deployed server is healthy — container
states and endpoint reachability — given its IP and an SSH credential.

## Inputs

- **Server IP** (required)
- **SSH user** (default `root`), **auth** (key path or password), port
  (default 22)

## How to run

```bash
.claude/skills/service-status/scripts/status.sh --host <ip> --key <path>
# or
.claude/skills/service-status/scripts/status.sh --host <ip> --password '<pw>'
```

## Output

- `docker|podman ps` for `booking-*` containers + per-container health
  state (db, minio, backend, frontend).
- Endpoint reachability from this machine: frontend (5173), backend
  schema (8000), swagger, MinIO health (9000).

Use this after a deploy/update, or to triage a server the user reports as
misbehaving.
