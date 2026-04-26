# Tasks

## Task 1: Common error envelope
- [x] Create `backend/common/__init__.py`
- [x] Create `backend/common/errors.py` with `DomainError`, `PermissionDeniedError`, `IllegalStateTransition`, `NotFoundError`, `ConflictError`
- [x] Add `custom_exception_handler` that wraps responses into `{detail, code, fields}`
- [x] Wire `REST_FRAMEWORK["EXCEPTION_HANDLER"]` in `config/settings.py`
- [x] Add `tests/common/test_error_envelope.py` smoke-testing the handler shape (4 tests)

## Task 2: Appointment state machine
- [x] Create `backend/appointments/state.py` with `ALLOWED_TRANSITIONS` and `assert_transition`
- [x] Update `appointments/views.py` to use the state machine through the services that wrap `assert_transition`
- [x] Add `tests/appointments/test_state.py` covering allowed and rejected transitions (9 tests)

## Task 3: Appointments service
- [x] Create `backend/appointments/services.py` with `create_appointment`, `confirm_appointment`, `complete_appointment`, `cancel_appointment`, `attach_completion_attachments`
- [x] Move role checks + slot/blocked validation + state transitions out of `AppointmentSerializer.validate` into the service
- [x] Shrink `AppointmentSerializer` to shape-only (only `validate_appointment_time` slot-membership remains)
- [x] Thin `appointments/views.py` so each handler does serializer → service → response
- [x] Verify pytest still green

## Task 4: Users service
- [x] Create `backend/users/services.py` with `create_user_with_role`, `update_user_with_role`, `suggest_username`, `assert_unique_username`, `assert_unique_email`, `assert_doctor_fields`, `change_password`, `logout`
- [x] Override `UserManageSerializer.build_field` to strip the auto-generated `UniqueValidator` from the `username` field so the service owns uniqueness
- [x] Move suggestion + doctor-phone checks out of `UserManageSerializer.validate` into the service
- [x] Replace `users/views.py:LogoutView` bare exception swallow with `services.logout()` that raises `ConflictError` on `TokenError` and is otherwise idempotent
- [x] Replace `ChangePasswordView` inline mutation with a call to `services.change_password()`
- [x] Replace `BaseRoleUserViewSet.perform_create/perform_update` to call `services.create_user_with_role` / `update_user_with_role`
- [x] Update `tests/users/test_user_management.py::test_duplicate_username_is_rejected` → `test_duplicate_username_returns_suggestion` and add `test_duplicate_username_suggests_next_free_suffix` (the suggestion is now reachable)

## Task 5: Documentation and verification
- [x] Update `README.md` change-chain to include `introduce-backend-service-layer`
- [x] `pytest` green — 47 passed in 3.46s (was 33; +9 state machine, +4 error envelope, +1 suggestion-suffix)
- [x] `ruff check . && black --check .` green
- [x] `python manage.py makemigrations --check --dry-run` clean
