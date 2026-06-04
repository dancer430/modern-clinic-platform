from __future__ import annotations

import pytest

from content.models import Department, DoctorProfile


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.mark.django_db
def test_admin_creates_department(admin_client):
    resp = admin_client.post(
        "/api/admin/content/departments/",
        {"name": "Cardio", "slug": "cardio", "summary": "h"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert resp.json()["slug"] == "cardio"


@pytest.mark.django_db
def test_admin_lists_unpublished(admin_client):
    Department.objects.create(name="X", slug="x", is_published=False)
    resp = admin_client.get("/api/admin/content/departments/")
    assert resp.status_code == 200
    assert any(d["slug"] == "x" for d in resp.json())


@pytest.mark.django_db
def test_admin_assigns_departments_to_doctor(admin_client, doctor_user):
    profile = DoctorProfile.objects.create(user=doctor_user)
    d1 = Department.objects.create(name="A", slug="a")
    d2 = Department.objects.create(name="B", slug="b")
    resp = admin_client.put(
        f"/api/admin/content/doctor-profiles/{doctor_user.id}/departments/",
        [
            {"department_id": d1.id, "is_primary": True},
            {"department_id": d2.id, "is_primary": False},
        ],
        format="json",
    )
    assert resp.status_code == 200, resp.content
    profile.refresh_from_db()
    assert profile.department_links.count() == 2


@pytest.mark.django_db
def test_admin_assign_rejects_multiple_primaries(admin_client, doctor_user):
    DoctorProfile.objects.create(user=doctor_user)
    d1 = Department.objects.create(name="A", slug="a")
    d2 = Department.objects.create(name="B", slug="b")
    resp = admin_client.put(
        f"/api/admin/content/doctor-profiles/{doctor_user.id}/departments/",
        [
            {"department_id": d1.id, "is_primary": True},
            {"department_id": d2.id, "is_primary": True},
        ],
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_admin_approve_copies_draft(admin_client, doctor_user):
    p = DoctorProfile.objects.create(
        user=doctor_user,
        bio_draft_html="<p>new</p>",
        bio_published_html="<p>old</p>",
        draft_status=DoctorProfile.DraftStatus.PENDING,
    )
    resp = admin_client.post(f"/api/admin/content/doctor-profiles/{doctor_user.id}/approve/")
    assert resp.status_code == 200, resp.content
    p.refresh_from_db()
    assert p.bio_published_html == "<p>new</p>"
    assert p.draft_status == DoctorProfile.DraftStatus.APPROVED
    assert p.is_published is True


@pytest.mark.django_db
def test_admin_reject_requires_note(admin_client, doctor_user):
    DoctorProfile.objects.create(user=doctor_user, draft_status=DoctorProfile.DraftStatus.PENDING)
    resp = admin_client.post(
        f"/api/admin/content/doctor-profiles/{doctor_user.id}/reject/", {}, format="json"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_admin_pending_review_list(admin_client, doctor_user):
    DoctorProfile.objects.create(user=doctor_user, draft_status=DoctorProfile.DraftStatus.PENDING)
    resp = admin_client.get("/api/admin/content/pending-reviews/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.django_db
def test_non_admin_cannot_access_admin_endpoints(authed_client):
    # authed_client is a doctor (per conftest)
    resp = authed_client.get("/api/admin/content/departments/")
    assert resp.status_code == 403
