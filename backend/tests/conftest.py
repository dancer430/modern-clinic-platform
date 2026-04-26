from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from tests.factories import AppointmentFactory, DoctorScheduleSlotFactory, UserFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_user(db):
    return UserFactory(role="admin", is_staff=True, is_superuser=True, username="admin")


@pytest.fixture
def doctor_user(db):
    return UserFactory(
        role="doctor", username="doc1", email="doc1@example.com", phone="13800000001"
    )


@pytest.fixture
def patient_user(db):
    return UserFactory(role="patient", username="pat1")


@pytest.fixture
def authed_client(api_client, doctor_user):
    api_client.force_authenticate(user=doctor_user)
    return api_client


@pytest.fixture
def appointment_factory():
    return AppointmentFactory


@pytest.fixture
def schedule_slot_factory():
    return DoctorScheduleSlotFactory
