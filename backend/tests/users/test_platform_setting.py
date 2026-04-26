from __future__ import annotations

import pytest


@pytest.mark.django_db
class TestPlatformSetting:
    def test_get_is_open_to_unauthenticated(self, api_client):
        response = api_client.get("/api/auth/platform/")
        assert response.status_code == 200
        assert "platform_name" in response.json()

    def test_patch_requires_admin(self, api_client, doctor_user):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.patch(
            "/api/auth/platform/",
            {"platform_name": "Hijack Clinic"},
            format="json",
        )
        assert response.status_code == 403

    def test_admin_can_update_name(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.patch(
            "/api/auth/platform/",
            {"platform_name": "Renamed Clinic"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["platform_name"] == "Renamed Clinic"
