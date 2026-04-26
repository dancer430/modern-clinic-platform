# Tasks

## Task 1: Backend test infrastructure
- [x] Add `backend/requirements-dev.txt` pinning pytest, pytest-django, factory_boy, ruff, black
- [x] Add `backend/pyproject.toml` with `[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.black]`
- [x] Create `backend/tests/__init__.py`, `backend/tests/conftest.py` with shared fixtures (`api_client`, `admin_user`, `doctor_user`, `patient_user`)
- [x] Create `backend/tests/factories.py` with `UserFactory`, `AppointmentFactory`, `DoctorScheduleSlotFactory`

## Task 2: Backend smoke tests
- [x] `tests/users/test_auth.py` — login by username/email, refresh, logout, me, change-password
- [x] `tests/users/test_user_management.py` — role-gated CRUD, duplicate-username rejection, role filter on list
- [x] `tests/users/test_platform_setting.py` — GET unauthenticated, PATCH role-gated
- [x] `tests/appointments/test_appointments.py` — create/confirm/complete/cancel + role gates + slot validation + blocked-slot rejection
- [x] `tests/appointments/test_schedule_slots.py` — doctor-owned creation, admin override, deletion gates

## Task 3: Backend lint baseline
- [x] Run `black backend/` and commit the reformat as one isolated commit (folded into the same commit as test infra; pure-format diff)
- [x] Resolve any ruff findings (auto-fix produced 6 import reorders, applied)

## Task 4: Frontend test infrastructure
- [x] Add vitest, @vue/test-utils, happy-dom to `frontend/package.json` devDependencies
- [x] Add `frontend/vitest.config.ts` extending `vite.config.ts` with `test.environment = 'happy-dom'`
- [x] Add `npm test` and `npm run test:run` scripts
- [x] Add `frontend/vitest.setup.ts` with an in-memory Storage shim (Node 25 ships an incomplete experimental `localStorage` global that breaks `clear()`)

## Task 5: Frontend unit tests
- [x] `frontend/src/features/appointments/composables/__tests__/useAppointmentsPage.spec.ts` — slotOptions, bookedCount, isBlocked, statusTagType (placed at `features/appointments/__tests__/`)
- [x] `frontend/src/utils/__tests__/tokenRefresh.spec.ts` — concurrent calls share one network request, success updates localStorage, failure rejects all callers, post-success the pending promise clears
- [x] Bonus: `frontend/src/features/appointments/__tests__/types.spec.ts` covering SLOT_TIMES / toLocalDateString / toApiTime

## Task 6: CI workflow
- [x] `.github/workflows/ci.yml` with three jobs (backend-tests, migrations-check, frontend-tests)
- [x] Trigger on PR to main and push to main
- [x] Concurrency group cancels superseded runs

## Task 7: Documentation
- [x] Update `docs/setup.md` with sections on running backend tests (`cd backend && pytest`) and frontend tests (`cd frontend && npm test`)
- [x] Update `README.md` change-chain section to include this sub-change and link to the master refactor spec

## Task 8: Verification
- [x] `pytest` green locally — 33 passed in 3.08s
- [x] `npm run test:run` green locally — 12 passed in ~900ms
- [x] `ruff check backend && black --check backend` exit 0
- [x] `npm run build` (vue-tsc + vite) green
- [ ] GitHub Actions run on a no-op PR shows three green jobs (verified locally; awaiting first push to main)
