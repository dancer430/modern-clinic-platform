# Establish Test and CI Baseline

## Why

The repository has zero automated test coverage on the backend (`appointments/tests.py` and `users/tests.py` are empty stubs) and zero on the frontend (`seed.spec.ts` is an unrelated Playwright stub). The next set of structural refactors planned in `docs/superpowers/specs/2026-04-26-clinic-platform-refactor-design.md` — auth/HTTP unification, feature migration, backend service layer, attachment storage rework — all change behavior of running code, and there is no safety net to detect regressions.

Adding the missing tests *during* those refactors would conflate two changes in every PR. We need the safety net first.

## What Changes

Install the minimal cross-stack test and CI baseline that the refactor program will run on top of:

- backend: pytest + pytest-django + factory_boy with smoke coverage of auth lifecycle, role-based user CRUD, appointment lifecycle/role gates/slot validation, and platform setting access
- frontend: vitest + @vue/test-utils + happy-dom with unit coverage of the existing `useAppointmentsPage` slot/booked derivation and a deduped-refresh contract test
- formatting and lint: ruff + black for Python; `vue-tsc` is already invoked by `npm run build`
- CI: a single GitHub Actions workflow running backend tests, frontend tests, and `vue-tsc` on every PR and on `main`

## Scope

In scope:
- adding pytest, pytest-django, factory_boy, ruff, black to backend dev dependencies
- adding vitest, @vue/test-utils, happy-dom to frontend dev dependencies
- writing the initial smoke tests (the floor, not the ceiling)
- a `.github/workflows/ci.yml` that runs the test suites and lint
- a `pytest.ini`/`pyproject.toml` config and a `vitest.config.ts` config
- documenting how to run tests locally in `docs/setup.md`

Out of scope:
- end-to-end Playwright tests (deferred; `seed.spec.ts` is left untouched until a later sub-change)
- 100% coverage; baseline is "every critical path has at least one test"
- mutation testing, property-based testing, contract testing
- container-based CI; the GitHub Actions runner uses native Python and Node
- any structural refactor of the code under test

## Expected Outcome

After this change:
- `pytest` from the `backend/` directory runs and passes
- `npm test` from `frontend/` runs and passes
- `gh pr` opens trigger CI that runs both suites and `vue-tsc`
- subsequent OpenSpec sub-changes in the refactor program inherit a green baseline they cannot regress without CI failing
