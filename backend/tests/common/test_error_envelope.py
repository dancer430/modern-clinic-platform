from __future__ import annotations

import pytest

from tests.factories import UserFactory


@pytest.mark.django_db
class TestErrorEnvelope:
    def test_unauthenticated_request_returns_envelope(self, api_client):
        response = api_client.get("/api/auth/me/")
        assert response.status_code == 401
        body = response.json()
        assert set(body.keys()) == {"detail", "code", "fields"}
        assert body["code"] == "not_authenticated"
        assert body["fields"] is None

    def test_permission_denied_returns_envelope(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        response = api_client.patch("/api/auth/platform/", {"platform_name": "x"}, format="json")
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "permission_denied"
        assert body["fields"] is None

    def test_validation_error_returns_envelope_with_fields(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        # Missing all required fields
        response = api_client.post("/api/appointments/", {}, format="json")
        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "validation_error"
        assert isinstance(body["fields"], dict)
        assert "patient" in body["fields"] or "doctor" in body["fields"]

    def test_login_failure_uses_error_code(self, api_client):
        UserFactory(username="frank", password="real-pw-1234")
        response = api_client.post(
            "/api/auth/login/",
            {"username": "frank", "password": "wrong"},
            format="json",
        )
        assert response.status_code == 401
        body = response.json()
        assert set(body.keys()) == {"detail", "code", "fields"}
        # SimpleJWT raises AuthenticationFailed; default_code is
        # "authentication_failed" or "no_active_account"
        assert body["code"] in {"authentication_failed", "no_active_account"}
