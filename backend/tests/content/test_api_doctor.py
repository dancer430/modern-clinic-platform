from __future__ import annotations

import pytest

from content.models import DoctorProfile


@pytest.fixture
def doctor_client(api_client, doctor_user):
    DoctorProfile.objects.create(user=doctor_user)
    api_client.force_authenticate(user=doctor_user)
    return api_client


@pytest.mark.django_db
def test_doctor_reads_own_profile(doctor_client):
    resp = doctor_client.get("/api/doctor/content/profile/me/")
    assert resp.status_code == 200
    assert resp.json()["draft_status"] == "none"


@pytest.mark.django_db
def test_doctor_updates_draft(doctor_client):
    resp = doctor_client.put(
        "/api/doctor/content/profile/me/",
        {"title": "Senior", "specialty": "Heart", "bio_draft_html": "<p>hi</p>"},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    assert resp.json()["bio_draft_html"] == "<p>hi</p>"


@pytest.mark.django_db
def test_doctor_submit_review_transitions_to_pending(doctor_client, doctor_user):
    resp = doctor_client.post("/api/doctor/content/profile/me/submit-review/")
    assert resp.status_code == 200
    assert DoctorProfile.objects.get(user=doctor_user).draft_status == "pending"


@pytest.mark.django_db
def test_doctor_cannot_edit_while_pending(doctor_client, doctor_user):
    p = DoctorProfile.objects.get(user=doctor_user)
    p.draft_status = DoctorProfile.DraftStatus.PENDING
    p.save()
    resp = doctor_client.put(
        "/api/doctor/content/profile/me/",
        {"title": "X"},
        format="json",
    )
    assert resp.status_code == 409


@pytest.mark.django_db
def test_doctor_cannot_access_other_doctor_via_admin_paths(doctor_client):
    resp = doctor_client.get("/api/admin/content/departments/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_unauth_cannot_access_doctor_self(api_client):
    resp = api_client.get("/api/doctor/content/profile/me/")
    assert resp.status_code in (401, 403)
