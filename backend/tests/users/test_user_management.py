from __future__ import annotations

import pytest

from tests.factories import UserFactory


@pytest.mark.django_db
class TestDoctorViewSet:
    def test_list_returns_only_doctors(self, api_client, admin_user):
        UserFactory(username="doc-a", role="doctor")
        UserFactory(username="doc-b", role="doctor")
        UserFactory(username="pat-x", role="patient")
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/auth/doctors/")
        assert response.status_code == 200
        usernames = sorted(item["username"] for item in response.json())
        assert usernames == ["doc-a", "doc-b"]

    def test_admin_can_create_doctor(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/auth/doctors/",
            {
                "username": "new-doc",
                "name": "New Doctor",
                "email": "newdoc@clinic.test",
                "phone": "13900000001",
                "password": "doc-pw-12345",
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        assert response.json()["role"] == "doctor"

    def test_patient_cannot_create_doctor(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        response = api_client.post(
            "/api/auth/doctors/",
            {"username": "evil-doc", "name": "Evil", "email": "e@x.com", "phone": "139"},
            format="json",
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestPatientViewSet:
    def test_doctor_can_create_patient(self, api_client, doctor_user):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.post(
            "/api/auth/patients/",
            {"username": "new-pat", "name": "New Patient"},
            format="json",
        )
        assert response.status_code == 201, response.json()
        assert response.json()["role"] == "patient"

    def test_duplicate_username_is_rejected(self, api_client, admin_user):
        UserFactory(username="dup", role="patient")
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            "/api/auth/patients/",
            {"username": "dup", "name": "Duplicate"},
            format="json",
        )
        assert response.status_code == 400
        body = response.json()
        assert "username" in body
        # NOTE: the serializer also defines a custom suggestion path that
        # currently never fires because DRF's auto-generated UniqueValidator
        # preempts it. The introduce-backend-service-layer sub-change will
        # consolidate this; for now we only lock the public contract.

    def test_list_returns_only_patients(self, api_client, admin_user):
        UserFactory(username="pat-only", role="patient")
        UserFactory(username="doc-skip", role="doctor")
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/auth/patients/")
        assert response.status_code == 200
        usernames = [item["username"] for item in response.json()]
        assert "pat-only" in usernames
        assert "doc-skip" not in usernames
