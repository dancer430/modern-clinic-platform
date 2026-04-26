from __future__ import annotations

import pytest

from appointments.models import Appointment
from appointments.state import ALLOWED_TRANSITIONS, assert_transition
from common.errors import IllegalStateTransition


class TestAppointmentStateTable:
    def test_pending_can_become_confirmed_or_cancelled(self):
        assert ALLOWED_TRANSITIONS[Appointment.Status.PENDING] == {
            Appointment.Status.CONFIRMED,
            Appointment.Status.CANCELLED,
        }

    def test_confirmed_can_become_completed_or_cancelled(self):
        assert ALLOWED_TRANSITIONS[Appointment.Status.CONFIRMED] == {
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
        }

    def test_completed_is_terminal(self):
        assert ALLOWED_TRANSITIONS[Appointment.Status.COMPLETED] == set()

    def test_cancelled_is_terminal(self):
        assert ALLOWED_TRANSITIONS[Appointment.Status.CANCELLED] == set()


class TestAssertTransition:
    def test_valid_transition_returns_none(self):
        assert assert_transition(Appointment.Status.PENDING, Appointment.Status.CONFIRMED) is None

    @pytest.mark.parametrize(
        "current,target",
        [
            (Appointment.Status.PENDING, Appointment.Status.COMPLETED),
            (Appointment.Status.COMPLETED, Appointment.Status.CANCELLED),
            (Appointment.Status.CANCELLED, Appointment.Status.CONFIRMED),
            (Appointment.Status.CONFIRMED, Appointment.Status.PENDING),
        ],
    )
    def test_invalid_transition_raises(self, current, target):
        with pytest.raises(IllegalStateTransition):
            assert_transition(current, target)
