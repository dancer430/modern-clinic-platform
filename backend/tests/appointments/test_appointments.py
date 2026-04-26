from __future__ import annotations

import datetime as dt

import pytest

from appointments.models import Appointment
from tests.factories import (
    AppointmentFactory,
    DoctorScheduleSlotFactory,
    UserFactory,
)


def _payload(patient, doctor, *, slot_time=dt.time(9, 0), date=None):
    appointment_date = date or (dt.date.today() + dt.timedelta(days=1))
    return {
        "patient": patient.id,
        "doctor": doctor.id,
        "appointment_date": appointment_date.isoformat(),
        "appointment_time": slot_time.isoformat(),
        "reason": "checkup",
    }


@pytest.mark.django_db
class TestCreateAppointment:
    def test_patient_creates_own_appointment(self, api_client, patient_user, doctor_user):
        api_client.force_authenticate(user=patient_user)
        response = api_client.post(
            "/api/appointments/", _payload(patient_user, doctor_user), format="json"
        )
        assert response.status_code == 201, response.json()
        assert response.json()["status"] == "pending"

    def test_patient_cannot_create_for_another_patient(self, api_client, patient_user, doctor_user):
        other = UserFactory(username="other-pat", role="patient")
        api_client.force_authenticate(user=patient_user)
        response = api_client.post(
            "/api/appointments/", _payload(other, doctor_user), format="json"
        )
        assert response.status_code == 403

    def test_rejects_time_outside_allowed_slots(self, api_client, patient_user, doctor_user):
        api_client.force_authenticate(user=patient_user)
        response = api_client.post(
            "/api/appointments/",
            _payload(patient_user, doctor_user, slot_time=dt.time(12, 15)),
            format="json",
        )
        assert response.status_code == 400

    def test_rejects_blocked_schedule_slot(self, api_client, patient_user, doctor_user):
        slot_date = dt.date.today() + dt.timedelta(days=1)
        DoctorScheduleSlotFactory(
            doctor=doctor_user,
            slot_date=slot_date,
            slot_time=dt.time(9, 0),
            is_available=False,
        )
        api_client.force_authenticate(user=patient_user)
        response = api_client.post(
            "/api/appointments/",
            _payload(patient_user, doctor_user, date=slot_date),
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestConfirmAppointment:
    def test_doctor_confirms_own(self, api_client, doctor_user, patient_user):
        appt = AppointmentFactory(doctor=doctor_user, patient=patient_user)
        api_client.force_authenticate(user=doctor_user)
        response = api_client.put(
            f"/api/appointments/{appt.id}/confirm/",
            {"confirm_info": "see you at 9am"},
            format="json",
        )
        assert response.status_code == 200
        appt.refresh_from_db()
        assert appt.status == Appointment.Status.CONFIRMED

    def test_other_doctor_cannot_confirm(self, api_client, doctor_user, patient_user):
        appt = AppointmentFactory(doctor=doctor_user, patient=patient_user)
        intruder = UserFactory(username="other-doc", role="doctor")
        api_client.force_authenticate(user=intruder)
        response = api_client.put(
            f"/api/appointments/{appt.id}/confirm/",
            {"confirm_info": "I'm taking over"},
            format="json",
        )
        assert response.status_code in (403, 404)
        appt.refresh_from_db()
        assert appt.status == Appointment.Status.PENDING


@pytest.mark.django_db
class TestCompleteAppointment:
    def test_complete_requires_confirmed_status(self, api_client, doctor_user, patient_user):
        appt = AppointmentFactory(doctor=doctor_user, patient=patient_user)
        api_client.force_authenticate(user=doctor_user)
        response = api_client.put(
            f"/api/appointments/{appt.id}/complete/",
            {"diagnosis_result": "fine", "treatment_plan": "rest"},
            format="json",
        )
        assert response.status_code == 400

    def test_complete_after_confirm_succeeds(self, api_client, doctor_user, patient_user):
        appt = AppointmentFactory(
            doctor=doctor_user,
            patient=patient_user,
            status=Appointment.Status.CONFIRMED,
        )
        api_client.force_authenticate(user=doctor_user)
        response = api_client.put(
            f"/api/appointments/{appt.id}/complete/",
            {"diagnosis_result": "ok", "treatment_plan": "rest"},
            format="json",
        )
        assert response.status_code == 200
        appt.refresh_from_db()
        assert appt.status == Appointment.Status.COMPLETED


@pytest.mark.django_db
class TestCancelAppointment:
    def test_patient_can_cancel_own_pending(self, api_client, doctor_user, patient_user):
        appt = AppointmentFactory(doctor=doctor_user, patient=patient_user)
        api_client.force_authenticate(user=patient_user)
        response = api_client.put(f"/api/appointments/{appt.id}/cancel/", {}, format="json")
        assert response.status_code == 200
        appt.refresh_from_db()
        assert appt.status == Appointment.Status.CANCELLED

    def test_unrelated_user_cannot_cancel(self, api_client, doctor_user, patient_user):
        appt = AppointmentFactory(doctor=doctor_user, patient=patient_user)
        outsider = UserFactory(username="outsider-pat", role="patient")
        api_client.force_authenticate(user=outsider)
        response = api_client.put(f"/api/appointments/{appt.id}/cancel/", {}, format="json")
        assert response.status_code in (403, 404)
        appt.refresh_from_db()
        assert appt.status == Appointment.Status.PENDING

    def test_cannot_cancel_completed_appointment(self, api_client, doctor_user, patient_user):
        appt = AppointmentFactory(
            doctor=doctor_user,
            patient=patient_user,
            status=Appointment.Status.COMPLETED,
        )
        api_client.force_authenticate(user=patient_user)
        response = api_client.put(f"/api/appointments/{appt.id}/cancel/", {}, format="json")
        assert response.status_code == 400
