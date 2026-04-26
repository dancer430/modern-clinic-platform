# Design: Test and CI Baseline

## Boundary

This change introduces test infrastructure and a CI workflow. It does not change application behavior, public APIs, models, or directory structure of the application code. It adds files under `backend/tests/`, `frontend/src/**/__tests__/`, and `.github/workflows/`.

## Motivation

The refactor program documented in `docs/superpowers/specs/2026-04-26-clinic-platform-refactor-design.md` plans six sub-changes that mutate behavior of running code. Without a baseline test suite that runs in CI, each of those PRs would be reviewed without any automated evidence that behavior is preserved. Building the safety net first is cheaper than threading test additions through every refactor PR.

## Backend test stack

- **Runner:** `pytest` with `pytest-django` for Django integration. Rejected `Django manage.py test` because pytest fixtures compose better and the team will lean on factories.
- **Factories:** `factory_boy`. Rejected hand-built fixtures because user/appointment graphs need composition (`UserFactory(role=...)`, `AppointmentFactory(status=...)`).
- **Layout:** `backend/tests/` as a top-level package with sub-packages mirroring app names (`tests/users/`, `tests/appointments/`). Rejected `<app>/tests.py` because we need package-level fixtures shared across the suite (e.g. an `api_client` fixture).
- **Config:** `backend/pyproject.toml` with `[tool.pytest.ini_options]`. Rejected `pytest.ini` because the same `pyproject.toml` will house ruff/black config, keeping all Python tooling in one file.
- **Coverage policy:** baseline ≥ 50% line coverage on `users/` and `appointments/`, measured but not enforced as a CI gate yet. The gate becomes ratchet-only in a later sub-change.

### Smoke tests included

| App | Test |
|---|---|
| auth | login by username succeeds; login by email resolves to username; refresh works; logout blacklists refresh token; me returns the current user; change-password rejects wrong current password |
| users | admin can create doctor; doctor can create patient; patient cannot create doctor; duplicate username returns suggestion; list endpoints filter by role |
| appointments | patient creates own appointment; patient cannot create for another; doctor confirms own appointment; doctor cannot confirm another doctor's; complete requires confirmed status; cancel allowed only for related users; slot outside `ALLOWED_SLOT_TIMES` rejected; blocked schedule slot rejects creation |
| platform-setting | unauthenticated GET allowed; non-admin PATCH forbidden; admin PATCH updates name |

These are smoke tests, not exhaustive. They lock the public contract of each route.

## Frontend test stack

- **Runner:** `vitest`. Rejected `jest` because the project is on Vite and shares config naturally.
- **Vue helpers:** `@vue/test-utils` for component mounting; `happy-dom` (lighter than jsdom) for DOM emulation.
- **Layout:** colocated `__tests__/*.spec.ts` next to the unit under test. Rejected a top-level `tests/` mirror because feature-local placement matches the boundary model already adopted.
- **Initial tests:**
  - `frontend/src/features/appointments/composables/__tests__/useAppointmentsPage.spec.ts` covers `slotOptions`, `bookedCount`, `isBlocked`, and `statusTagType`.
  - `frontend/src/utils/__tests__/tokenRefresh.spec.ts` covers the deduplicated refresh promise (concurrent calls share one network request).

The token-refresh test is included now even though `unify-auth-client-responsibilities` will move the file later — it pins the contract that *concurrent 401s share one refresh*. When the file moves, the test moves with it.

## Lint and format stack

- **Python:** `ruff` for lint, `black` for format. Rejected `flake8 + isort + pylint` because ruff replaces all three with one config and one binary.
- **TypeScript/Vue:** `vue-tsc` is already invoked by `npm run build`. Adding `eslint` is deferred to a later sub-change to keep this baseline change focused.

## CI workflow

`.github/workflows/ci.yml` runs three jobs in parallel:

1. `backend-tests` — checkout, setup Python 3.12, `pip install -r requirements.txt -r requirements-dev.txt`, `pytest`, `ruff check .`, `black --check .` (working dir: `backend/`).
2. `frontend-tests` — checkout, setup Node 20, `npm ci`, `npm test -- --run`, `npm run build` (which runs `vue-tsc -b`).
3. `migrations-check` — `python manage.py makemigrations --check --dry-run` to catch model drift.

Triggers: `pull_request` against `main` and `push` to `main`. Concurrency group keyed on `${{ github.workflow }}-${{ github.ref }}` with cancel-in-progress so superseded PR pushes drop their old runs.

## Risks

- pytest-django requires `DJANGO_SETTINGS_MODULE`; in dev that's `config.settings`. After `harden-settings-and-attachments` lands, it becomes `config.settings.dev`. The baseline ships with `config.settings` and the later sub-change updates `pyproject.toml`.
- factory_boy 3.x requires `Faker` — we accept the transitive dep.
- happy-dom occasionally lags behind browser APIs; if a needed API is missing we fall back to jsdom in a follow-up.
- adding ruff/black on a codebase that wasn't formatted by them will surface a one-time large diff. We run `black .` once and commit the result inside this sub-change.

## Mitigations

- All new dependencies pinned to exact versions in `requirements-dev.txt` and `package.json` so CI is deterministic.
- The initial `black` reformat is committed in a single dedicated commit so subsequent diffs stay readable.
- ruff is configured with a permissive starting rule set (`E`, `F`, `I`, `B`) so the baseline doesn't drown the team in lint debt.

## Verification

This sub-change is successful when:
- `pytest` runs green from `backend/` with at least 14 tests covering the smoke matrix above
- `npm test -- --run` runs green from `frontend/` with at least 5 tests
- `ruff check .` and `black --check .` exit 0 on `backend/`
- the GitHub Actions workflow runs all three jobs successfully on a no-op PR
- `docs/setup.md` documents `pytest` and `npm test` invocation

## Rollback

The sub-change ships as one PR. Rollback is `git revert` of that PR. No data migration, no application behavior change, so rollback is risk-free.
