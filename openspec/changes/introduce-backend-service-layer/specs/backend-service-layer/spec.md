## ADDED Requirements

### Requirement: Backend mutations shall be performed by service functions
The backend SHALL route every state-changing operation (appointment lifecycle, user-role provisioning, password change, logout) through a function in `<app>/services.py`. Views MUST NOT mutate model fields or call `instance.save(...)` directly for cross-aggregate workflows.

#### Scenario: Confirming an appointment
- **WHEN** a doctor confirms an assigned appointment via `PUT /api/appointments/{id}/confirm/`
- **THEN** the view MUST delegate to `appointments.services.confirm_appointment(...)` and the service MUST be the only place that flips the status, persists `confirm_info`, and saves the row

#### Scenario: Creating a doctor or patient
- **WHEN** an admin POSTs to `/api/auth/doctors/` or a doctor POSTs to `/api/auth/patients/`
- **THEN** the view MUST call `users.services.create_user_with_role(...)` and the service MUST own role assignment, password defaulting, and uniqueness assertion

### Requirement: Appointment status transitions shall be governed by an explicit table
The backend SHALL define an `ALLOWED_TRANSITIONS` table that maps each `Appointment.Status` to the set of statuses it may move to, and SHALL reject any attempted transition not present in that table.

#### Scenario: Trying to cancel a completed appointment
- **WHEN** a request asks to cancel an appointment whose current status is `completed`
- **THEN** the service MUST raise `IllegalStateTransition` and the view MUST return HTTP 400 with `code = "illegal_state_transition"`

#### Scenario: Trying to complete a pending appointment
- **WHEN** a request asks to complete an appointment whose current status is `pending`
- **THEN** the service MUST raise `IllegalStateTransition` (skipping the confirm step) and the view MUST return HTTP 400

### Requirement: Backend errors shall use a uniform JSON envelope
Every error response from the backend SHALL include `detail`, `code`, and `fields` keys. `fields` MUST be non-null only when the error is a serializer shape-validation error.

#### Scenario: Permission denied on a workflow action
- **WHEN** a user without permission attempts an appointment action
- **THEN** the response MUST be `{"detail": "<message>", "code": "permission_denied", "fields": null}` with HTTP 403

#### Scenario: Shape-validation failure on a request body
- **WHEN** a request body fails serializer field validation
- **THEN** the response MUST include `code = "validation_error"` and `fields` populated with DRF's per-field error dict

### Requirement: Username suggestion shall be reachable on duplicates
The backend SHALL surface a non-conflicting username suggestion when a `username` collision is detected during user creation.

#### Scenario: Creating a patient with a taken username
- **WHEN** a request to `POST /api/auth/patients/` collides on `username`
- **THEN** the response MUST be HTTP 400 with `fields = {"username": ["...try '<suggestion>'"]}` where `<suggestion>` is the next-available numeric suffix on the requested base
