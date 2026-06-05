from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from appointments.models import Appointment
from tests.factories import UserFactory
from users.models import User


@pytest.fixture
def operator_user(db):
    return UserFactory(role=User.Role.OPERATOR, username="operator1")


@pytest.fixture
def operator_client(operator_user):
    client = APIClient()
    client.force_authenticate(user=operator_user)
    return client


@pytest.fixture
def patient_client(patient_user):
    client = APIClient()
    client.force_authenticate(user=patient_user)
    return client


@pytest.mark.django_db
def test_operator_lists_all_appointments(operator_client, doctor_user, patient_user):
    Appointment.objects.create(
        patient=patient_user,
        doctor=doctor_user,
        appointment_date="2026-06-10",
        appointment_time="09:00",
        created_by=patient_user,
    )
    resp = operator_client.get("/api/appointments/")
    assert resp.status_code == 200
    assert resp.data["count"] >= 1


@pytest.mark.django_db
def test_operator_cannot_create_appointment(operator_client, doctor_user, patient_user):
    resp = operator_client.post(
        "/api/appointments/",
        {
            "patient": patient_user.id,
            "doctor": doctor_user.id,
            "appointment_date": "2026-06-10",
            "appointment_time": "09:00",
        },
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_operator_cannot_confirm(operator_client, doctor_user, patient_user):
    appt = Appointment.objects.create(
        patient=patient_user,
        doctor=doctor_user,
        appointment_date="2026-06-10",
        appointment_time="09:00",
        status="pending",
        created_by=patient_user,
    )
    resp = operator_client.put(
        f"/api/appointments/{appt.id}/confirm/",
        {"confirm_info": "x"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_contact_fields_role_gated(operator_client, patient_client, doctor_user, patient_user):
    patient_user.phone = "13800001234"
    patient_user.email = "p@example.com"
    patient_user.save()
    doctor_user.phone = "13900005678"
    doctor_user.save()
    Appointment.objects.create(
        patient=patient_user,
        doctor=doctor_user,
        appointment_date="2026-06-10",
        appointment_time="09:00",
        created_by=patient_user,
    )
    # Operator (privileged) should see contact fields
    row = operator_client.get("/api/appointments/").data["results"][0]
    assert row["patient_phone"] == "13800001234"
    assert row["patient_email"] == "p@example.com"
    assert row["doctor_phone"] == "13900005678"

    # Patient should see blank contact fields
    patient_row = patient_client.get("/api/appointments/").data["results"][0]
    assert patient_row["patient_phone"] == ""
