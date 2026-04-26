"""Explicit appointment status transitions.

The previous implementation re-stated the rule "PENDING → CONFIRMED → COMPLETED,
PENDING/CONFIRMED → CANCELLED, terminal otherwise" inside three different view
handlers. Centralizing the table makes the rule one fact, not three.
"""

from __future__ import annotations

from common.errors import IllegalStateTransition

from .models import Appointment

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    Appointment.Status.PENDING: {Appointment.Status.CONFIRMED, Appointment.Status.CANCELLED},
    Appointment.Status.CONFIRMED: {Appointment.Status.COMPLETED, Appointment.Status.CANCELLED},
    Appointment.Status.COMPLETED: set(),
    Appointment.Status.CANCELLED: set(),
}


def assert_transition(current: str, target: str) -> None:
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise IllegalStateTransition(
            f"Cannot transition appointment from '{current}' to '{target}'",
        )
