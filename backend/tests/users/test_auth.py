from __future__ import annotations

import pytest

from tests.factories import UserFactory


@pytest.mark.django_db
class TestLogin:
    def test_login_by_username_returns_tokens_and_user(self, api_client):
        UserFactory(username="alice", password="strong-pass-1", role="patient")
        response = api_client.post(
            "/api/auth/login/",
            {"username": "alice", "password": "strong-pass-1"},
            format="json",
        )
        assert response.status_code == 200
        body = response.json()
        assert "access" in body
        assert "refresh" in body
        assert body["user"]["username"] == "alice"
        assert body["user"]["user_type"] == "patient"

    def test_login_by_email_resolves_to_username(self, api_client):
        UserFactory(username="bob", email="bob@clinic.test", password="another-pass-9")
        response = api_client.post(
            "/api/auth/login/",
            {"username": "bob@clinic.test", "password": "another-pass-9"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "bob"

    def test_login_with_wrong_password_returns_401(self, api_client):
        UserFactory(username="carol", password="real-secret")
        response = api_client.post(
            "/api/auth/login/",
            {"username": "carol", "password": "wrong"},
            format="json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestRefresh:
    def test_refresh_rotates_tokens(self, api_client):
        UserFactory(username="dan", password="pw-12345")
        login = api_client.post(
            "/api/auth/login/",
            {"username": "dan", "password": "pw-12345"},
            format="json",
        )
        refresh_token = login.json()["refresh"]
        response = api_client.post("/api/auth/refresh/", {"refresh": refresh_token}, format="json")
        assert response.status_code == 200
        assert "access" in response.json()


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, api_client):
        UserFactory(username="eve", password="pw-12345")
        login = api_client.post(
            "/api/auth/login/",
            {"username": "eve", "password": "pw-12345"},
            format="json",
        )
        access = login.json()["access"]
        refresh = login.json()["refresh"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_response = api_client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
        assert logout_response.status_code == 200

        api_client.credentials()
        retry = api_client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        assert retry.status_code == 401


@pytest.mark.django_db
class TestMe:
    def test_me_returns_current_user(self, api_client, doctor_user):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get("/api/auth/me/")
        assert response.status_code == 200
        body = response.json()
        assert body["username"] == doctor_user.username
        assert body["user_type"] == "doctor"

    def test_me_requires_authentication(self, api_client):
        response = api_client.get("/api/auth/me/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestChangePassword:
    def test_correct_current_password_succeeds(self, api_client):
        user = UserFactory(username="frank", password="old-pw-1234")
        api_client.force_authenticate(user=user)
        response = api_client.post(
            "/api/auth/change-password/",
            {
                "current_password": "old-pw-1234",
                "new_password": "new-pw-stronger-9",
                "confirm_password": "new-pw-stronger-9",
            },
            format="json",
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password("new-pw-stronger-9")

    def test_wrong_current_password_returns_400(self, api_client):
        user = UserFactory(username="grace", password="old-pw-1234")
        api_client.force_authenticate(user=user)
        response = api_client.post(
            "/api/auth/change-password/",
            {
                "current_password": "wrong",
                "new_password": "new-pw-stronger-9",
                "confirm_password": "new-pw-stronger-9",
            },
            format="json",
        )
        assert response.status_code == 400
