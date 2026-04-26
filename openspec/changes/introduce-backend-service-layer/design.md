# Design: Backend Service Layer

## Boundary

This change introduces three new module boundaries in the Django backend (`common/`, `*/services.py`, `appointments/state.py`) and re-draws the responsibilities of three existing layers (serializers, views, permissions). It does not change the database schema, the authentication backend, or the URL surface.

## Motivation

Today the backend's business logic is co-resident with two unrelated concerns:

1. **DRF serializers as domain validators.** `AppointmentSerializer.validate` rejects appointments based on doctor role, patient role, slot whitelist membership, and `DoctorScheduleSlot.is_available`. The first two are role invariants, the third is a domain rule, and only the slot-whitelist check is true field validation.
2. **DRF views as state machines.** `AppointmentViewSet.{confirm,complete,cancel}` each re-derive the same role check (`is_admin or appointment.doctor_id == user.id`), each gate on a hard-coded prior status, and each `appointment.save(update_fields=[...])`. There is no single place that says "completed appointments cannot be cancelled" or "only the assigned doctor can complete".

When the next sub-changes need to (a) change attachment storage, (b) add role-aware guards on the frontend that mirror the backend, and (c) extend error responses with structured codes, they will collide head-on with this layout. Hence: extract a service layer first.

## Target structure

```text
backend/
  common/
    __init__.py
    errors.py            # DomainError hierarchy + drf exception handler
    pagination.py        # shared PageNumberPagination defaults
  users/
    services.py          # NEW: user-role + auth workflows
    serializers.py       # SHRUNK: shape only
    views.py             # SHRUNK: serializer → service → response
  appointments/
    services.py          # NEW: appointment lifecycle workflows
    state.py             # NEW: explicit state transition table
    serializers.py       # SHRUNK
    views.py             # SHRUNK
```

## Layer contracts

### Serializers
- Input: raw request data. Output: typed fields.
- Allowed: `required`, `min_length`, regex, choices, set membership (e.g. `appointment_time in ALLOWED_SLOT_TIMES`), date-range, type coercion.
- Forbidden: querying other models, computing role-based behavior, performing `instance.save()` for cross-aggregate workflows.

### Services
- Functions, not classes (services are stateless; class wrappers add no value here).
- Signature: `def create_appointment(*, patient: User, doctor: User, when: datetime, reason: str, created_by: User) -> Appointment`.
- May raise `DomainError` subclasses; must not raise `serializers.ValidationError` (that's a view-layer concept).
- Single transactional boundary per call (`@transaction.atomic` on each mutating service function).
- Owns role authorization via small helpers (`assert_can_confirm(actor, appointment)`).

### State machine

`appointments/state.py` exposes:

```python
ALLOWED_TRANSITIONS: dict[Status, set[Status]] = {
    Status.PENDING:   {Status.CONFIRMED, Status.CANCELLED},
    Status.CONFIRMED: {Status.COMPLETED, Status.CANCELLED},
    Status.COMPLETED: set(),
    Status.CANCELLED: set(),
}

def assert_transition(current: Status, target: Status) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise IllegalStateTransition(current=current, target=target)
```

Services call `assert_transition` instead of re-stating the rule.

### Views
- Authenticated; permission_classes still gate "any access" vs "anonymous".
- View body is roughly: deserialize → `service.do_thing(**serializer.validated_data, actor=request.user)` → serialize result.
- `try/except DomainError` is handled by the global exception handler, not per-view.

### Error envelope

```json
{
  "detail": "Only the responsible doctor or an admin can confirm",
  "code": "permission_denied",
  "fields": null
}
```

`fields` is non-null only for shape-validation errors raised by serializers, where it carries DRF's per-field error dict. Clients can switch on `code` without parsing prose.

## Domain error taxonomy

```python
class DomainError(Exception):
    code: str = "domain_error"
    status_code: int = 400
    default_message: str = "Domain error"

    def __init__(self, message: str | None = None, *, fields: dict | None = None):
        super().__init__(message or self.default_message)
        self.fields = fields

class PermissionDeniedError(DomainError):
    code = "permission_denied"
    status_code = 403
    default_message = "Permission denied"

class IllegalStateTransition(DomainError):
    code = "illegal_state_transition"
    status_code = 400

class NotFoundError(DomainError):
    code = "not_found"
    status_code = 404

class ConflictError(DomainError):
    code = "conflict"
    status_code = 409
```

Used sparingly. Most validation still comes from serializers.

## DRF exception handler

`common/errors.py:custom_exception_handler` first delegates to DRF's default handler (so `ValidationError` still gives `{field: [...]}` shape we wrap into `fields`), then catches `DomainError` and renders the envelope. Wired in `settings.py` via `REST_FRAMEWORK['EXCEPTION_HANDLER']`.

## Consequences for tests

- Existing 33 tests stay green because the public response shape stays the same: `400`/`403`/`404` semantics are preserved; `detail` text may shift slightly. Tests that asserted on `response.status_code` keep passing; tests that asserted on `response.json()['detail']` may need a tweak.
- The duplicate-username test gets *strengthened*: `test_duplicate_username_is_rejected` becomes `test_duplicate_username_returns_suggestion` because the serializer no longer auto-validates uniqueness — the service does, and produces the suggestion before raising.

## Migration sequencing

1. Land `common/errors.py` + the exception handler with no service layer yet. Verify all existing tests still green (the new envelope is backward-compatible with the existing shape because we *add* `code`/`fields`, not replace `detail`).
2. Add `appointments/state.py` and route `confirm`/`complete`/`cancel` views through `assert_transition`. No service layer yet. Verify tests green.
3. Extract `appointments/services.py` and route the views through it. Shrink `AppointmentSerializer.validate` to slot-whitelist + type checks only. Verify tests green.
4. Extract `users/services.py`. Shrink `UserManageSerializer.validate` to whitespace/required-only; move uniqueness + suggestion + doctor-phone check into `users/services.py`. Update `test_duplicate_username_is_rejected` to assert on the suggestion. Verify tests green.
5. Replace `users/views.py:LogoutView` bare `except Exception: pass` with a service call that raises `ConflictError` on bad refresh tokens; the global handler renders the envelope.

Each step is a separate commit. Bisecting stays useful.

## Risks

- **Response shape drift.** Adding `code`/`fields` could surprise clients that strictly typed the response. Mitigation: the frontend currently does `error.response?.data?.detail` everywhere; it ignores extra keys. Tests at the contract boundary catch any drift.
- **Hidden DRF magic.** DRF's `ModelSerializer` auto-adds a `UniqueValidator` for `unique=True` fields (which is exactly what currently masks the suggestion path). Mitigation: explicitly `validators = []` on the username field in `UserManageSerializer` so the service is the only uniqueness path.
- **Transaction boundaries.** `complete_appointment` mutates the appointment AND bulk-creates attachments. The service wraps both in `@transaction.atomic`, matching today's implicit behavior (DRF runs the action handler inside a request transaction in many configs, but Django defaults to autocommit).
- **Test friction.** Refactor tends to reveal latent bugs (e.g. the dead username-suggestion path). We accept new tests as part of this sub-change rather than separate-PRing them.

## Verification

- `pytest` green.
- `ruff` + `black --check` green.
- `python manage.py makemigrations --check --dry-run` exits 0 (no schema change).
- A spot-check curl against `/api/appointments/{id}/confirm/` while not the responsible doctor returns `{"detail": "...", "code": "permission_denied", "fields": null}` with HTTP 403.

## Rollback

Single-PR rollback. No DB migration. `git revert` removes the new modules and restores the old serializer/view bodies.
