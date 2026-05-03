# Clinic Platform Full-Stack Refactor — Top-Level Design

Status: Approved-by-delegation (user is AFK; user authorized the assistant to proceed on its recommended path; this document is the authoritative top-level spec for the refactor program).

Date: 2026-04-26
Owner: ruiqiu (qiurui)
Top-level program name: `clinic-platform-refactor`

This spec is the umbrella for a multi-part refactor of the medical booking platform. It does not replace the OpenSpec change governance defined in `docs/internal/change-governance.md`; instead it decomposes the user's "from frontend to backend complete optimization refactor" request into a sequence of OpenSpec changes that each follow the existing governance.

The terminology used throughout: *master spec* = this document; *sub-change* = an OpenSpec change under `openspec/changes/<name>/`. The implementation plan for each sub-change is its `tasks.md`.

## 1. Why now

The repository is functional but has crossed several discomfort thresholds at once:

- frontend has two overlapping HTTP clients (`utils/axios.ts` and `utils/apiClient.ts`) that both attach access tokens, both refresh on 401, and both `clearTokens()` on refresh failure outside the auth store
- backend business logic is co-mingled with serializer validation (appointment role checks, slot conflict checks, attachment shape checks, `connection.vendor != "postgresql"` runtime gating)
- 0 automated tests on either side; `seed.spec.ts` is an empty Playwright stub
- attachments are stored as base64 in `TextField` and are gated by DB vendor
- only the appointments page has been moved into `features/`; `Doctors`, `Patients`, `TimeSlots`, `Records`, `Profile` still live under `views/`
- there is no role-aware routing guard (any authenticated user can reach any page)
- settings live in a single 149-line `settings.py` with no environment-variable validation and no logging configuration

The user has already drafted three OpenSpec changes that solve the structural pieces of this list (`standardize-frontend-feature-boundaries`, `modularize-appointment-page-flow`, `unify-auth-client-responsibilities`). This refactor program completes those, then adds the missing pieces.

## 2. Non-goals

- redesign of the product or UX
- introduction of multi-tenancy, internationalization, or new business capabilities
- swapping frameworks (Django stays, Vue 3 stays, Element Plus stays, Pinia stays)
- adopting a backend-for-frontend layer
- adding Celery/Redis unless concretely required by attachments hardening

If a non-goal becomes necessary later, it should be its own OpenSpec change — not a silent expansion of this program.

## 3. Architectural target

### 3.1 Frontend target

```text
frontend/src/
  app/                      # router, app shell, global initialization
    router/
    main.ts (moved here from src/)
  shared/
    http/                   # one axios instance + one refresh promise
    ui/                     # element-plus wrappers, BrandLogo, etc.
    utils/                  # generic helpers
    types/                  # cross-feature primitives
  features/
    auth/
      api/        services/        store/        types/
    appointments/           # already mostly here
      api/        components/      composables/  pages/        types/
    doctors/      patients/      timeslots/      records/      profile/
```

Rules already locked in by `standardize-frontend-feature-boundaries`:

- pages live with the owning feature; the router only registers them
- pinia stores default to features; `auth` is a feature, not a `stores/` global
- HTTP transport is shared, business endpoints are feature-local
- cross-feature dependencies cross only through public surface

### 3.2 Backend target

```text
backend/
  config/
    settings/
      base.py        # everything not env-dependent
      dev.py         # SQLite, debug
      prod.py        # Postgres, validated env, logging
    urls.py
  users/
    models.py        serializers.py        views.py        urls.py
    services/        # NEW: UserService, AuthService
    selectors.py     # NEW: read queries
  appointments/
    models.py        serializers.py        views.py        urls.py
    services/        # AppointmentService, ScheduleService, AttachmentService
    state.py         # explicit appointment state machine
    selectors.py
  common/            # NEW: error handling, pagination, mixins
    errors.py        # standard error response shape
    pagination.py
    permissions.py
  tests/             # NEW: pytest layout (per-app sub-packages)
```

Layering rule: views are thin; serializers validate shape only; services own business invariants; selectors own read queries with explicit `select_related`/`prefetch_related`.

### 3.3 Data flow

Request → DRF view → serializer (shape validation) → service (invariants, state transitions, persistence) → response.

Errors raised by services derive from a small set of typed exceptions in `common/errors.py`; the DRF exception handler converts them to a standard JSON shape `{detail, code, fields?}` so the frontend `shared/http` layer can normalize errors uniformly.

### 3.4 Auth/HTTP target

- one `shared/http/client.ts` axios instance
- one `shared/http/refresh.ts` promise-deduplicated refresh
- `features/auth/services/session.ts` owns persistence (localStorage), expiry, and scheduling
- `features/auth/store/` owns reactive user/role state and exposes high-level actions
- the HTTP client *reads* the access token via a callback the auth feature registers; it does not import the store

This is exactly what `unify-auth-client-responsibilities` already specifies — this master spec just commits to executing it.

## 4. Decomposition into OpenSpec sub-changes

In recommended implementation order:

### 4.1 `establish-test-and-ci-baseline` (NEW)

Purpose: install the safety net before structural surgery.

Backend: pytest + pytest-django + factory_boy; smoke tests on auth (login/refresh/logout/me/change-password), users (doctor/patient CRUD + role permissions), appointments (lifecycle + role gates + slot validation), platform setting. Coverage target: ~70% on services/views once they exist; for now baseline ~50%.

Frontend: vitest + @vue/test-utils + happy-dom; unit tests on `useAppointmentsPage` slot/booked logic, status tag mapping, and the soon-to-exist `shared/http` refresh deduplication.

CI: GitHub Actions running on PRs and `main`: `backend-tests`, `frontend-build-and-test`, ruff + black --check on Python, `vue-tsc` (already in `build`).

Deliverable: every later sub-change runs under green CI before merging.

### 4.2 `unify-auth-client-responsibilities` (already designed)

Purpose: collapse `utils/axios.ts` + `utils/apiClient.ts` + `utils/tokenRefresh.ts` + `stores/auth.ts` into `shared/http/` + `features/auth/`. Remove `clearTokens()`'s direct `window.location.href` jump in favor of an auth-feature logout that the HTTP client signals via an injected callback.

### 4.3 `modularize-appointment-page-flow` finishing batch

Purpose: the migration is partially done (router points to `features/appointments/pages/AppointmentsPage.vue`, components/composable/api/types exist) but is uncommitted and the old `views/AppointmentsPage.vue` is deleted only on the working tree. We commit the migration, point appointments' `api.ts` at `shared/http` (after 4.2), drop unused `api/images.ts`, add a vitest covering `useAppointmentsPage` slot derivation.

### 4.4 `migrate-remaining-pages-to-features` (NEW)

Purpose: migrate `Doctors`, `Patients`, `TimeSlots`, `Records`, `Profile` views to `features/<name>/{api,pages,components,composables,types}` using appointments as the template. Adds role-aware route guards: each route declares `meta.roles?: Array<'admin'|'doctor'|'patient'>` and the shell guard rejects unauthorized roles to `/dashboard` with a toast.

### 4.5 `introduce-backend-service-layer` (NEW)

Purpose: add `users/services/`, `appointments/services/`, `appointments/state.py`, `common/errors.py`, `common/pagination.py`. Move from serializers/views into services:

- `AppointmentService.create / confirm / complete / cancel` (owns role checks + state transitions)
- `ScheduleService.is_blocked / list_for(role)`
- `AttachmentService.attach(appointment, items, uploader)` with size + MIME guards
- `UserService.create_with_role`, `suggest_username`
- `AuthService.logout(refresh_token)`

`AppointmentSerializer` keeps shape-level validation only (e.g. `appointment_time in ALLOWED_SLOT_TIMES`); the role-of-doctor / role-of-patient checks move to the service.

### 4.6 `harden-settings-and-attachments` (NEW)

Purpose:

- split `config/settings.py` into `base/dev/prod`, validate env vars (`POSTGRES_*`, `DJANGO_SECRET_KEY` in prod) using `django-environ` (preferred over a new pydantic dep, since django-environ is purpose-built and small)
- add structured logging (JSON in prod, console in dev)
- migrate `AppointmentAttachment.image_data: TextField` → `image: ImageField(upload_to=...)`; remove the `connection.vendor != "postgresql"` gate; remove the SQLite-mode UI hint that depends on `db_vendor` leak in `UserSerializer`
- migrate `User.avatar_data` and `PlatformSetting.logo_data` similarly to `ImageField`
- add MIME validation by content (`python-magic-bin` is too heavy; use `Pillow` for image format probing; backend already uses Pillow indirectly via Django's `ImageField`)
- bump dependencies: `django-environ`, `Pillow`, `pytest`, `pytest-django`, `factory_boy`, `ruff`, `black`

This is a database-changing sub-change; we ship a one-shot data migration that converts existing base64 rows to files in `MEDIA_ROOT`. Provide a backout migration that reads the file back into base64 for emergency rollback.

## 5. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Migration #4.6 corrupts attachments | dry-run script + reversible RunPython; back up `db.sqlite3`/Postgres before applying |
| Service-layer extraction (#4.5) changes API responses subtly | snapshot tests on response JSON before extraction (in #4.1) |
| Token refresh deduplication regression in #4.2 | vitest covering 2 concurrent 401 → 1 refresh call (added in #4.1 baseline + tightened in #4.2) |
| `features/` migration breaks router prefetch order | each migrated page lands behind its existing route name; e2e smoke (Playwright) added in #4.1 |
| Settings split breaks `init-stack.sh` | `init-stack.sh` already sets `ENV=production`; `DJANGO_SETTINGS_MODULE` becomes `config.settings.prod` and the script is updated in the same sub-change |

## 6. Rollback strategy

Each sub-change is delivered as a single `feature/<change-name>` branch landing as one PR. Rollback = `git revert` of that PR. Database migrations in #4.6 ship reversible `RunPython` operations. CI added in #4.1 includes a "rollback test": revert the merge, run the test suite locally, ensure green.

## 7. Verification

The program is successful when:

- `pytest` and `vitest` both run green in CI on every PR
- only one axios instance and one refresh promise exist in the codebase
- every page lives under `features/`; `views/` is empty or removed
- role-based route guards reject mismatched roles
- backend services are the only place that mutates state; serializers do not call `.save()` on cross-aggregate updates
- attachments are files on the local filesystem under `MEDIA_ROOT`, not base64 in `TextField` (object storage is intentionally out of scope; the file storage abstraction is `django.core.files.storage.default_storage` so a future swap is a settings-level change)
- settings load through validated environment in production and fail loudly when misconfigured
- the OpenSpec changes that this program references are all archived under `openspec/changes/archive/`

## 8. Sequencing summary

```
1. establish-test-and-ci-baseline
2. unify-auth-client-responsibilities          (depends on 1)
3. modularize-appointment-page-flow finish     (depends on 2 for shared/http)
4. migrate-remaining-pages-to-features         (depends on 3 as template)
5. introduce-backend-service-layer             (parallelizable with 3-4 once 1 lands)
6. harden-settings-and-attachments             (last; depends on 5 for AttachmentService)
```

Each sub-change ends with: green CI, OpenSpec change archived, README/roadmap updated.

## 9. Out-of-scope follow-ups (future)

These are noted but explicitly not part of this program:

- swapping JWT for session+CSRF on cookie domain (security follow-up)
- replacing Element Plus with a design-system that supports dark mode end-to-end
- moving frontend to Nuxt for SSR
- introducing Celery/Redis for image compression jobs
- pagination/filtering uniformity across all list endpoints (only appointments is paginated today)
- soft-delete + audit log

If any of these are pulled forward, raise a new OpenSpec change rather than expanding scope here.
