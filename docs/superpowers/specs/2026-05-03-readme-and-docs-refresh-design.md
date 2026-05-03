---
title: README and Docs Refresh for Out-of-the-Box Onboarding
date: 2026-05-03
status: approved
audience: internal team new hires
language: English (no translation)
---

# README and Docs Refresh for Out-of-the-Box Onboarding

## 1. Goal

A new internal team member should be able to clone this repository, follow the
top of `README.md`, and reach a working three-role demo (admin / doctor /
patient flow) within ~30 minutes. The current docs do not meet this bar:

- `frontend/README.md` is still the default Vite template — no project info.
- `backend/` has no README at all.
- Root `README.md` mixes governance/change-chain content with onboarding
  content, making the "first 5 minutes" path noisy.
- `docs/setup.md` covers the happy path but has no Troubleshooting section,
  so any first-run failure (port conflict, mirror unreachable, etc.) leaves
  new hires stuck.
- The Dockerfiles pin `docker-mirrors.alauda.cn/library/...` — fine inside
  the corporate network, but breaks for anyone working off-network. Per
  decision Q7-C, this is left as a documented Troubleshooting workaround,
  not a code change.

## 2. Non-Goals

- No code changes: Dockerfiles, compose files, `init-stack.sh`,
  `cleanup-stack.sh`, `.env.example`, and backend/frontend source stay
  untouched.
- No new seed/demo command. Default account guidance is limited to the
  admin user that the bootstrap script already creates from `.env`.
- No translation. All docs stay English (decision Q2-A).
- No restructuring of `openspec/` or `docs/superpowers/`.
- No screenshots or marketing-style content.

## 3. Audience and Decisions Recap

| Question | Choice | Implication |
|---|---|---|
| Q1 audience | B — internal new hires | Keep alauda mirror; assume Docker/Compose available; English. |
| Q2 language | A — English only | No bilingual content. |
| Q3 default accounts | A — admin only from `.env` | Document `admin` login; doctor/patient created via admin UI. |
| Q4 governance content | A — move to `docs/internal/` | Root README keeps a one-line pointer. |
| Q5 troubleshooting depth | B — medium (10 entries) | Includes mirror swap, Podman/Docker toggle, DB reset. |
| Q6 sub-READMEs | B — self-contained | `backend/README.md` and `frontend/README.md` ~80 lines each. |
| Q7 Dockerfile mirror | C — docs only | Mirror swap lives in Troubleshooting, not in Dockerfile. |

## 4. File Plan

### 4.1 `README.md` (root) — rewrite

Section order:

1. **Title + one-line positioning** — Django + Vue 3 healthcare scheduling
   platform, three roles, full appointment lifecycle.
2. **Quick Start (3 commands)** — `cp .env.example .env`, edit secrets,
   `sh ./init-stack.sh`. Show the three access URLs (frontend 5173, API 8000,
   Swagger 8000/api/docs/swagger/).
3. **Default Login** — username comes from `DJANGO_SUPERUSER_USERNAME`,
   password from `DJANGO_SUPERUSER_PASSWORD`. Note that doctor/patient
   accounts are created from the admin UI after first login.
4. **Tech Stack** — keep current content.
5. **Project Layout** — refresh tree to match the actual directory listing
   (include `init-stack.sh`, `cleanup-stack.sh`, `openspec/`, `docs/`,
   `docs/internal/`, `docs/superpowers/`).
6. **Module READMEs** — pointers to `backend/README.md` and
   `frontend/README.md`.
7. **Dev Workflow Convention** — keep current 6-step Git flow.
8. **Further Reading** — three bullets:
   - `docs/setup.md` — full setup, validation, and troubleshooting
   - `docs/internal/` — change governance, roadmap, product overview
   - `docs/superpowers/specs/` — active refactor program

Drop from current README:
- The 8-line OpenSpec change-chain list (now reachable via
  `docs/internal/change-roadmap.md`).
- The `docs/superpowers/specs/2026-04-26-...` direct link in the body
  (kept once at the bottom under Further Reading).

Target length: ~110 lines.

### 4.2 `docs/setup.md` — extend

Keep sections 1–6 (Quick Start / Env Vars / Local non-Docker / Validation /
Tests / Core API). Update:

- Section 1.3 Access URLs: confirmed against `docker-compose.yml`.
- Section 4.1 Tests: keep current pytest/ruff/black + vitest/vue-tsc commands.

Add **section 7: Troubleshooting** with these 10 entries (each ≤ 10 lines,
problem statement + fix command(s)):

1. Port 8000 or 5173 already in use → `lsof -i :8000` + stop conflicting
   process or change `ports:` mapping in `docker-compose.yml`.
2. `docker-compose` v1 `KeyError: 'ContainerConfig'` → install Compose v2
   (`docker compose version`); v1 is unsupported.
3. Container name conflict (`booking-db` / `booking-backend` /
   `booking-frontend` already exists) → `sh ./cleanup-stack.sh`, then
   re-init.
4. Admin login fails after first boot → check `DJANGO_SUPERUSER_*` were
   set BEFORE first `up`; if changed mid-run, run
   `docker compose exec backend python manage.py changepassword <user>`.
5. Frontend 5173 blank / 502 from nginx → confirm `frontend` container is
   up; check `docker compose logs -f frontend`; rebuild with
   `docker compose up -d --build frontend`.
6. DB reset / wipe → `sh ./cleanup-stack.sh --purge-data` (irreversible),
   then re-init.
7. Migration failure on bootstrap → `docker compose logs -f backend`,
   identify the failing migration, fix model/migration, then
   `docker compose exec backend python manage.py migrate`.
8. Frontend `npm run build` fails (node 20 / cache issues) → delete
   `frontend/node_modules` and `frontend/package-lock.json` for the
   container build path, or `docker compose build --no-cache frontend`.
9. Podman vs Docker — auto-detected by `init-stack.sh`; force with
   `sh ./init-stack.sh --runtime=podman` or `--runtime=docker`.
10. **Alauda mirror unreachable** (off-network) → in `backend/Dockerfile`
    and `frontend/Dockerfile`, replace
    `docker-mirrors.alauda.cn/library/` with `docker.io/library/` (3
    occurrences total: `python:3.12-slim`, `node:20-alpine`,
    `nginx:1.27-alpine`). Then `docker compose build --no-cache`. Note
    this is a local-only change; do not commit.

Cross-link from root README "Quick Start" to "Section 7 Troubleshooting".

Target length: ~250 lines.

### 4.3 `backend/README.md` — new file (self-contained, ~80 lines)

Sections:

1. **What this is** — Django 4.2 + DRF API for the booking platform.
2. **Module map** — bullet list of `config/`, `users/`, `appointments/`,
   `common/`, `tests/`, `scripts/`. One sentence per module describing
   its responsibility, sourced from current code (no invention).
3. **Local dev (venv + SQLite)** — copy/paste block: create venv, install
   `requirements.txt` + `requirements-dev.txt`, copy `.env.example` to
   `.env`, `manage.py migrate`, `manage.py createsuperuser`,
   `manage.py runserver`.
4. **Docker dev** — one paragraph pointing back to root README + setup.md.
5. **Tests, lint, format** — table:
   - `pytest` — full suite
   - `pytest -k <pattern>` — focused
   - `pytest --cov` — coverage
   - `ruff check .` — lint
   - `ruff check . --fix` — lint with auto-fix
   - `black --check .` — format check
   - `black .` — format
6. **Migrations** — `makemigrations`, `migrate`, `showmigrations`,
   `sqlmigrate <app> <name>`.
7. **Bootstrap script** — describe `scripts/bootstrap-backend.sh`: waits
   for DB, runs `migrate`, idempotently creates superuser if all three
   `DJANGO_SUPERUSER_*` env vars are present, then starts gunicorn.
8. **OpenAPI schema** — `manage.py spectacular --file schema.yaml` to
   regenerate; `/api/docs/swagger/` to browse.
9. **Debugging** — three bullets: backend logs
   (`docker compose logs -f backend`), Django shell
   (`manage.py shell`), DB shell
   (`docker compose exec db psql -U <user> -d <db>`).

Verify the module map against actual `backend/` structure before writing
prose. If a module exists but its purpose is unclear, write the directory
name with a one-line "see source" instead of inventing a description.

### 4.4 `frontend/README.md` — rewrite (overwrite Vite template, ~80 lines)

Sections:

1. **What this is** — Vue 3 + TS + Vite admin console for the booking
   platform.
2. **Directory map** — bullet list of `src/features/`, `src/api/`,
   `src/router/`, `src/stores/`, `src/components/`, `src/views/`,
   `src/composables/` (whatever exists), `src/utils/`. One sentence per
   directory, verified against actual `frontend/src/` listing.
3. **Local dev** — `npm install`, `npm run dev`, default Vite port 5173.
4. **Docker dev** — pointer to root README + setup.md.
5. **Tests, typecheck, build** — table:
   - `npm run test` — vitest watch
   - `npm run test:run` — vitest one-shot (used in CI)
   - `npm run typecheck` — `vue-tsc -b --noEmit`
   - `npm run build` — typecheck + production build
   - `npm run preview` — preview built assets
6. **Conventions** — short pointers to:
   - Feature boundary rule (link to
     `openspec/changes/standardize-frontend-feature-boundaries/`)
   - Unified auth + HTTP client (link to
     `openspec/changes/unify-auth-client-responsibilities/`)
7. **Auto-imports** — `auto-imports.d.ts` and `components.d.ts` are
   generated by `unplugin-auto-import` / `unplugin-vue-components`; do
   not edit by hand.
8. **Debugging** — three bullets: vite dev proxy (point at backend at
   `http://127.0.0.1:8000`), reproducing token-refresh failure (clear
   localStorage), running a single vitest file
   (`npm run test:run -- src/path/to/file.spec.ts`).

Verify directory map against actual `frontend/src/` before writing prose.

### 4.5 `docs/internal/` — new subdirectory

Move (with `git mv` so history is preserved):

- `docs/change-governance.md` → `docs/internal/change-governance.md`
- `docs/change-roadmap.md` → `docs/internal/change-roadmap.md`
- `docs/PRODUCT_OVERVIEW.md` → `docs/internal/PRODUCT_OVERVIEW.md`

Create `docs/internal/README.md` (~30 lines) with one short paragraph
("This directory holds internal-team-only docs: change governance,
roadmap, product overview, and pointers to the active refactor specs.")
plus four bulleted links:

- `change-governance.md`
- `change-roadmap.md`
- `PRODUCT_OVERVIEW.md`
- `../superpowers/specs/` (active refactor program)

Update all in-repo links that pointed to the old paths. At minimum:

- root `README.md` — update / remove governance and roadmap links.
- `docs/setup.md` — currently has no inbound link to those files;
  verify with `grep -rn "PRODUCT_OVERVIEW\|change-governance\|change-roadmap" .`
  before committing.
- `openspec/` — same grep; if any change file references the old paths,
  update them.

## 5. Architecture and Data Flow

This is a documentation-only change. No runtime architecture is altered.
The only structural change is `docs/` gaining an `internal/`
subdirectory; all other files stay where they are.

## 6. Verification

Before claiming the change is complete:

1. **Link check** — run `grep -rn "docs/change-governance\|docs/change-roadmap\|docs/PRODUCT_OVERVIEW" .`
   from repo root and confirm no stale references remain (excluding the
   commit message and this spec file).
2. **Render check** — open every modified/created `.md` in a Markdown
   viewer (or `gh` preview) and confirm headings, code blocks, and
   internal links render.
3. **Quick Start dry-run** — read the rewritten root README top-to-bottom
   and verify a developer with only `git`, `docker`, `docker compose v2`
   on their machine can follow it without jumping to other files until
   the "Further Reading" section.
4. **Sub-README accuracy** — for both `backend/README.md` and
   `frontend/README.md`, every directory mentioned in the module map
   must actually exist. Run `ls backend/ frontend/src/` and reconcile.
5. **Troubleshooting commands** — every command in section 7 of
   `setup.md` must be syntactically valid (`docker compose ...` form, not
   `docker-compose`); paths (`backend/Dockerfile`, `frontend/Dockerfile`)
   must exist; cleanup script flags must match `cleanup-stack.sh`'s
   actual `--purge-data` flag.

## 7. Risks

- **Stale links elsewhere in the repo** — moving three files into
  `docs/internal/` will break any link that referenced the old path.
  Mitigation: pre-move grep, post-move grep.
- **Sub-README drift** — module maps written today will go stale as the
  refactor program continues. Mitigation: keep descriptions terse and
  pointer-based ("see source"), avoid restating what file headers
  already say. Reviewers should expect to update these when feature
  boundaries shift.
- **Troubleshooting accuracy** — a wrong command in Troubleshooting is
  worse than no Troubleshooting. Mitigation: every command verified
  against the actual scripts and compose file before commit.

## 8. Rollback

Pure documentation change. To roll back:

```sh
git revert <commit-sha>
```

No data, schema, or runtime impact.

## 9. Out of Scope (for follow-ups)

- A `seed_demo` management command for doctor/patient demo accounts
  (Q3-C path, declined this round).
- Parameterizing the Dockerfile registry via `ARG IMAGE_REGISTRY`
  (Q7-B path, declined this round).
- Bilingual (zh-CN) versions of root README / setup.md (Q2-D path,
  declined this round).
- Screenshots, architecture diagrams, or a CONTRIBUTING.md.
