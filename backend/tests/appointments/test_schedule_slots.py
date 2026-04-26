from __future__ import annotations

import datetime as dt

import pytest

from tests.factories import DoctorScheduleSlotFactory, UserFactory


@pytest.mark.django_db
class TestScheduleSlots:
    def test_doctor_creates_own_slot(self, api_client, doctor_user):
        api_client.force_authenticate(user=doctor_user)
        slot_date = dt.date.today() + dt.timedelta(days=2)
        response = api_client.post(
            "/api/schedule-slots/",
            {
                "doctor": doctor_user.id,
                "slot_date": slot_date.isoformat(),
                "slot_time": "09:00:00",
                "is_available": False,
            },
            format="json",
        )
        assert response.status_code == 201, response.json()

    def test_doctor_cannot_create_slot_for_another_doctor(self, api_client, doctor_user):
        other = UserFactory(username="other-doc", role="doctor")
        api_client.force_authenticate(user=doctor_user)
        slot_date = dt.date.today() + dt.timedelta(days=2)
        response = api_client.post(
            "/api/schedule-slots/",
            {
                "doctor": other.id,
                "slot_date": slot_date.isoformat(),
                "slot_time": "09:00:00",
                "is_available": False,
            },
            format="json",
        )
        assert response.status_code == 403

    def test_admin_can_delete_any_slot(self, api_client, admin_user):
        slot = DoctorScheduleSlotFactory()
        api_client.force_authenticate(user=admin_user)
        response = api_client.delete(f"/api/schedule-slots/{slot.id}/")
        assert response.status_code == 204

    def test_doctor_only_lists_own_slots(self, api_client, doctor_user):
        DoctorScheduleSlotFactory(doctor=doctor_user)
        DoctorScheduleSlotFactory()
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get("/api/schedule-slots/")
        assert response.status_code == 200
        body = response.json()
        ids = [item["doctor"] for item in body]
        assert all(doctor_id == doctor_user.id for doctor_id in ids)
        assert len(ids) == 1
