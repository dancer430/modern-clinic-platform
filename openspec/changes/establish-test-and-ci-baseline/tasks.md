# Tasks

## Task 1: Backend test infrastructure
- [ ] Add `backend/requirements-dev.txt` pinning pytest, pytest-django, factory_boy, ruff, black
- [ ] Add `backend/pyproject.toml` with `[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.black]`
- [ ] Create `backend/tests/__init__.py`, `backend/tests/conftest.py` with shared fixtures (`api_client`, `admin_user`, `doctor_user`, `patient_user`)
- [ ] Create `backend/tests/factories.py` with `UserFactory`, `AppointmentFactory`, `DoctorScheduleSlotFactory`

## Task 2: Backend smoke tests
- [ ] `tests/users/test_auth.py` — login by username/email, refresh, logout, me, change-password
- [ ] `tests/users/test_user_management.py` — role-gated CRUD, duplicate-username suggestion, role filter on list
- [ ] `tests/users/test_platform_setting.py` — GET unauthenticated, PATCH role-gated
- [ ] `tests/appointments/test_appointments.py` — create/confirm/complete/cancel + role gates + slot validation + blocked-slot rejection
- [ ] `tests/appointments/test_schedule_slots.py` — doctor-owned creation, admin override, deletion gates

## Task 3: Backend lint baseline
- [ ] Run `black backend/` and commit the reformat as one isolated commit
- [ ] Resolve any ruff findings or list as `# noqa` with comment if intentional

## Task 4: Frontend test infrastructure
- [ ] Add vitest, @vue/test-utils, happy-dom to `frontend/package.json` devDependencies
- [ ] Add `frontend/vitest.config.ts` extending `vite.config.ts` with `test.environment = 'happy-dom'`
- [ ] Add `npm test` script

## Task 5: Frontend unit tests
- [ ] `frontend/src/features/appointments/composables/__tests__/useAppointmentsPage.spec.ts` — slotOptions, bookedCount, isBlocked, statusTagType
- [ ] `frontend/src/utils/__tests__/tokenRefresh.spec.ts` — concurrent calls share one network request, success updates localStorage, failure rejects all callers

## Task 6: CI workflow
- [ ] `.github/workflows/ci.yml` with three jobs (backend-tests, frontend-tests, migrations-check)
- [ ] Trigger on PR to main and push to main
- [ ] Concurrency group cancels superseded runs

## Task 7: Documentation
- [ ] Update `docs/setup.md` with sections on running backend tests (`cd backend && pytest`) and frontend tests (`cd frontend && npm test`)
- [ ] Update `README.md` change-chain section to include this sub-change

## Task 8: Verification
- [ ] `pytest` green locally (≥ 14 tests)
- [ ] `npm test -- --run` green locally (≥ 5 tests)
- [ ] `ruff check backend && black --check backend` exit 0
- [ ] GitHub Actions run on a no-op PR shows three green jobs
