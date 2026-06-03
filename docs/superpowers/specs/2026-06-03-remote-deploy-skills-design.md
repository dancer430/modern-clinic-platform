# Remote Deploy Skill Suite — Design

Date: 2026-06-03
Status: Approved (design), pending implementation

## Goal

Add project skills that, given a target server IP plus an SSH password
**or** key path, perform the full Medical Booking Platform bring-up on
that server remotely — wrapping the existing `init-stack.sh` /
`docker-compose.yml` workflow over SSH.

## Deliverables

```
.claude/skills/
├── service-deploy/      SKILL.md + scripts/deploy.sh    # fresh provisioning
├── service-status/      SKILL.md + scripts/status.sh    # read-only health check
├── service-update/      SKILL.md + scripts/update.sh    # rolling update
└── service-common/      remote.sh + envgen.sh           # shared lib (no SKILL.md)
```

`service-common/` has no `SKILL.md`, so it is not loaded as a standalone
skill — it only holds shared shell functions sourced by the three
operation scripts, keeping each operation DRY.

## Connection layer — `service-common/remote.sh`

Runtime inputs (environment variables, set by the operation script from
the user-supplied values):

- `HOST` — server IP (required)
- `SSH_USER` — default `root`
- `SSH_PORT` — default `22`
- Exactly one of `SSH_KEY` (path to private key) or `SSH_PASSWORD`

Auth handling:

- Key: `ssh -i "$SSH_KEY"`.
- Password: prefer `sshpass -p`; if `sshpass` is absent (common on
  macOS), fall back to an `expect` wrapper (ships with macOS).
- First connect uses `StrictHostKeyChecking=accept-new`.

Functions: `test_conn`, `remote_run "<cmd>"`, `remote_push <local> <remote>`
(rsync over ssh, fallback `scp -r`). All honor a global `DRY_RUN=1` that
prints the remote command instead of executing it.

## `.env` generation — `service-common/envgen.sh`

Generates a production `.env` on the server from `.env.example` with
strong random secrets. Env contract verified against
`backend/config/settings.py`:

- `REQUIRED_PROD_ENV` = `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
  `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`.
- `DJANGO_SECRET_KEY` must differ from the dev default or prod startup
  raises `ImproperlyConfigured`.

Generated / set values:

- `ENV=production`, `DJANGO_DEBUG=0`
- `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `DJANGO_SUPERUSER_PASSWORD`,
  `MINIO_ROOT_PASSWORD` — each `openssl rand` derived
- `DJANGO_ALLOWED_HOSTS=<ip>,localhost,127.0.0.1`
- `POSTGRES_DB/USER=clinic`, `POSTGRES_HOST=db`, `POSTGRES_PORT=5432`
- `DJANGO_SUPERUSER_USERNAME=admin`, `DJANGO_SUPERUSER_EMAIL`
- `MINIO_ROOT_USER=clinic`, `MINIO_BUCKET=clinic-media`,
  `MINIO_ENDPOINT=http://minio:9000`,
  `MINIO_PUBLIC_ENDPOINT=http://<ip>:9000`
- `DJANGO_CORS_ALLOWED_ORIGINS=http://<ip>:5173` (defensive; the SPA is
  same-origin through the nginx `/api/` proxy, so CORS is not normally
  triggered — no CSRF setting is required)
- Build mirrors left at `.env.example` defaults (China mirrors)

The generated admin password + MinIO credentials are written to a LOCAL
gitignored file `./.deploy-credentials/<ip>.env` and summarized to the
user. They are never committed.

## service-deploy flow

1. Validate inputs; `test_conn`; confirm `sudo` works.
2. Re-run guard: if remote `~/clinic-platform/.env` exists OR `booking-*`
   containers are running, refuse and point to `service-update` — unless
   `--force`. Never overwrites `.env` or data volumes without `--force`.
3. Deliver code:
   - `push` (default): rsync current checkout to `~/clinic-platform/`,
     excluding `node_modules`, `.venv`, `db.sqlite3`, `.git`, `media`.
   - `clone`: `git clone <--repo>` on the server.
4. Generate `.env` (see envgen) with the server IP injected.
5. Run `sh ./init-stack.sh` on the server.
6. Verify: poll `http://<ip>:8000/api/schema/` = 200, `http://<ip>:5173/`
   = 200, container health. Report access URLs + credentials.

## service-status flow

Read-only. SSH in, run `docker|podman compose ps` + container health,
curl health endpoints from both server and local sides, print a status
table (container, port, backend/frontend/MinIO health). No side effects.

## service-update flow

1. Refuse if no existing deployment.
2. Deliver latest code, **preserving `.env` and data volumes**.
3. `compose build backend frontend` + `up -d` (idempotent `init-stack.sh`
   re-run); backend bootstrap runs migrations on start.
4. Verify health.

## Safety boundaries

Aligns with the user's AFK-delegation preference (land safe parts, stop
at irreversible ops):

- deploy never overwrites existing `.env` / volumes without `--force`.
- Suite contains no teardown / `--purge-data` — destructive data ops are
  out of scope by design.
- Credentials only land in a local gitignored file, never in the repo.

## Testing strategy

Shell scripts: `shellcheck` clean; every operation supports `--dry-run`
(prints remote commands, no connection). SSH paths are validated against
a real host manually — not unit-tested. `.deploy-credentials/` is added
to `.gitignore`.

## Open defaults (confirmed with user)

- SSH default user: `root` (overridable via `SSH_USER`).
- Remote code dir: `~/clinic-platform`.
