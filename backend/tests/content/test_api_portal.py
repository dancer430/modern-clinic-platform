from __future__ import annotations

import pytest

from content.models import Department, DoctorDepartment, DoctorProfile


@pytest.fixture
def published_dept(db):
    return Department.objects.create(
        name="Cardiology", slug="cardio", summary="hearts", is_published=True
    )


@pytest.fixture
def hidden_dept(db):
    return Department.objects.create(name="Hidden", slug="hidden", summary="x", is_published=False)


@pytest.fixture
def published_doctor(db, doctor_user, published_dept):
    p = DoctorProfile.objects.create(
        user=doctor_user,
        title="Dr.",
        specialty="Heart",
        bio_published_html="<p>hi</p>",
        is_published=True,
    )
    DoctorDepartment.objects.create(doctor=p, department=published_dept, is_primary=True)
    return p


@pytest.mark.django_db
def test_portal_departments_excludes_unpublished(api_client, published_dept, hidden_dept):
    resp = api_client.get("/api/portal/departments/")
    assert resp.status_code == 200
    slugs = [d["slug"] for d in resp.json()]
    assert "cardio" in slugs
    assert "hidden" not in slugs


@pytest.mark.django_db
def test_portal_departments_limit(api_client, db):
    for i in range(10):
        Department.objects.create(name=f"D{i}", slug=f"d{i}", is_published=True)
    resp = api_client.get("/api/portal/departments/?limit=5")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


@pytest.mark.django_db
def test_portal_department_detail_includes_doctors(api_client, published_doctor, published_dept):
    resp = api_client.get(f"/api/portal/departments/{published_dept.slug}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["department"]["slug"] == "cardio"
    assert len(body["doctors"]) == 1
    assert body["doctors"][0]["title"] == "Dr."


@pytest.mark.django_db
def test_portal_doctor_detail_no_auth_needed(api_client, published_doctor):
    resp = api_client.get(f"/api/portal/doctors/{published_doctor.user_id}/")
    assert resp.status_code == 200
    assert resp.json()["bio_published_html"] == "<p>hi</p>"


@pytest.mark.django_db
def test_portal_doctor_list_filters_unpublished(api_client, doctor_user, published_dept):
    DoctorProfile.objects.create(user=doctor_user, is_published=False)
    resp = api_client.get("/api/portal/doctors/")
    assert resp.status_code == 200
    assert resp.json() == []
