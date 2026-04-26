# Introduce Backend Service Layer

## Why

Backend business logic is currently split across DRF serializers and viewsets in a way that makes it hard to test, reuse, or change safely:

- `appointments/serializers.py:AppointmentSerializer.validate` enforces doctor-role/patient-role invariants and queries `DoctorScheduleSlot` to reject blocked slots — that is workflow logic, not field validation.
- `appointments/views.py` carries the appointment state machine inline: each of `confirm`/`complete`/`cancel` re-implements role checks, current-status guards, and field updates. The state machine has no single home.
- `users/serializers.py:UserManageSerializer.validate` mixes shape validation (strip whitespace, required fields) with workflow logic (suggest a non-conflicting username, enforce doctor-only phone uniqueness). The suggestion path is currently dead because DRF's auto-generated `UniqueValidator` preempts the custom check (locked by the test `test_duplicate_username_is_rejected`).
- `users/views.py:LogoutView` swallows all exceptions on token blacklist with a bare `except Exception: pass`.
- Error responses are inconsistent: most endpoints return DRF's default field-error dict, but `confirm`/`complete`/`cancel` return `{detail: "..."}` with English text only, and the serializer uses `raise serializers.ValidationError(string)` (which renders as `{non_field_errors: [...]}`) in some places and `raise serializers.ValidationError({field: "..."})` in others.

The next refactor sub-changes (`migrate-remaining-pages-to-features`, `harden-settings-and-attachments`) will lean on the backend's behavior, so we need a clear seam first.

## What Changes

Introduce a small, layered backend that pushes invariants into services and standardizes error responses:

- `backend/common/errors.py` defines a small set of typed domain exceptions and a DRF exception handler that maps them to a uniform JSON shape `{detail, code, fields?}`.
- `backend/users/services.py` owns `create_user_with_role`, `suggest_username`, `change_password`, `logout` (refresh-token blacklist).
- `backend/appointments/services.py` owns `create_appointment`, `confirm_appointment`, `complete_appointment`, `cancel_appointment`, `attach_completion_attachments`. Each of these is the single place that mutates state and the single place that decides who is allowed to.
- `backend/appointments/state.py` enumerates the explicit appointment state transition table; the services consult it instead of re-implementing status guards.
- Serializers shrink to shape-and-format validation only.
- Views become thin: validate input shape via serializer, call service, return serialized output.
- The custom username-suggestion path becomes reachable: `UserManageSerializer` defers uniqueness to the service so DRF's UniqueValidator no longer preempts it.

## Scope

In scope:
- `backend/common/`, `backend/users/services.py`, `backend/appointments/services.py`, `backend/appointments/state.py`
- shrinking serializers (`UserManageSerializer`, `AppointmentSerializer`, the action serializers) to remove business logic
- thinning views to serializer → service → response
- standardized error JSON shape and a DRF exception handler
- updating tests where behavior contracts shift (e.g. duplicate-username now returns the suggestion message)

Out of scope:
- changing model schema (no migrations in this sub-change)
- changing JWT/auth backends
- swapping DRF for anything else
- introducing async tasks or queues
- attachment storage migration (deferred to `harden-settings-and-attachments`)
- adding new endpoints

## Expected Outcome

After this change:
- every backend mutation path is reached through a service function whose name is a verb on the domain (`create_appointment`, `confirm_appointment`)
- views never read or mutate model fields directly
- the appointment state machine is one table, not five inline status guards
- errors come back as `{detail, code, fields?}` regardless of which view was called
- the existing 33 pytest tests still pass; the duplicate-username test is updated to assert the suggestion (now reachable)
- service modules are independently importable and testable without instantiating a `Request`
