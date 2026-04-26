## ADDED Requirements

### Requirement: Backend behavior shall be covered by an automated smoke suite
The repository SHALL run a backend automated test suite that exercises every public REST endpoint at least once with the role-based permission paths that exist for that endpoint.

#### Scenario: Auth lifecycle is exercised
- **WHEN** the backend test suite runs
- **THEN** it MUST cover login by username, login by email, refresh-token rotation, logout (refresh-token blacklist), `GET /me`, and password change with both correct and incorrect current password

#### Scenario: Role-based gates are exercised
- **WHEN** the backend test suite runs
- **THEN** it MUST cover at least one allowed and one rejected path for each role on each protected endpoint that has role logic (user CRUD, appointment confirm/complete/cancel, schedule-slot CRUD, platform-setting PATCH)

#### Scenario: Appointment slot rules are exercised
- **WHEN** the backend test suite runs
- **THEN** it MUST cover rejection of an appointment outside `ALLOWED_SLOT_TIMES` and rejection of an appointment whose target slot is marked unavailable in `DoctorScheduleSlot`

### Requirement: Frontend critical pure logic shall be covered by unit tests
The repository SHALL run a frontend unit test suite that covers pure logic which has multiple branches and is reused across UI surfaces.

#### Scenario: Appointment slot derivation is exercised
- **WHEN** the frontend test suite runs
- **THEN** it MUST cover `slotOptions`, `bookedCount`, and `isBlocked` derivation in `useAppointmentsPage` for at least: no doctor selected, doctor selected with zero conflicts, doctor selected with a blocked slot, doctor selected with a booked-but-not-blocked slot

#### Scenario: Token refresh deduplication is exercised
- **WHEN** the frontend test suite runs
- **THEN** it MUST cover that two concurrent `refreshAccessToken` calls trigger only one network request and that both callers receive the same resolved access token

### Requirement: CI shall block merges on test or build failure
The repository SHALL run an automated CI workflow that blocks merge when the backend tests, frontend tests, frontend type-check (`vue-tsc -b`), or Django `makemigrations --check` fails.

#### Scenario: A pull request introduces a failing backend test
- **WHEN** a pull request is opened against `main`
- **AND** the backend pytest suite fails for any reason
- **THEN** the CI status MUST be red and the PR MUST be marked as failing checks

#### Scenario: A pull request introduces a model change without a migration
- **WHEN** a pull request is opened against `main`
- **AND** `python manage.py makemigrations --check --dry-run` would create new migration files
- **THEN** the CI status MUST be red

### Requirement: Backend code style shall be enforceable by tooling
The repository SHALL include configuration that allows `ruff check` and `black --check` to run successfully against the entire `backend/` tree.

#### Scenario: Lint is run locally
- **WHEN** a contributor runs `ruff check backend/` followed by `black --check backend/`
- **THEN** both MUST exit with status zero on a clean checkout of `main`
