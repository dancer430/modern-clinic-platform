from __future__ import annotations

import pytest

from content.models import Department, DoctorProfile


@pytest.mark.django_db
def test_sitemap_lists_published_only(api_client, doctor_user):
    Department.objects.create(name="A", slug="a", is_published=True)
    Department.objects.create(name="H", slug="h", is_published=False)
    DoctorProfile.objects.create(user=doctor_user, is_published=True)
    resp = api_client.get("/sitemap.xml")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "/portal/departments/a" in body
    assert "/portal/departments/h" not in body
    assert f"/portal/doctors/{doctor_user.id}" in body
