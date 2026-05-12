from __future__ import annotations

import pytest
from django.db import IntegrityError

from content.models import Department, DoctorProfile


@pytest.mark.django_db
def test_department_slug_is_unique():
    Department.objects.create(name="Internal Medicine", slug="internal-medicine")
    with pytest.raises(IntegrityError):
        Department.objects.create(name="Other", slug="internal-medicine")


@pytest.mark.django_db
def test_department_defaults_unpublished_and_order_zero():
    d = Department.objects.create(name="Cardiology", slug="cardiology")
    assert d.is_published is False
    assert d.display_order == 0


@pytest.mark.django_db
def test_doctor_profile_one_per_user(doctor_user):
    DoctorProfile.objects.create(user=doctor_user)
    with pytest.raises(IntegrityError):
        DoctorProfile.objects.create(user=doctor_user)


@pytest.mark.django_db
def test_doctor_profile_defaults(doctor_user):
    p = DoctorProfile.objects.create(user=doctor_user)
    assert p.draft_status == DoctorProfile.DraftStatus.NONE
    assert p.is_published is False
    assert p.bio_published_html == ""
    assert p.bio_draft_html == ""


@pytest.mark.django_db
def test_doctor_department_pair_is_unique(doctor_user):
    from content.models import DoctorDepartment

    profile = DoctorProfile.objects.create(user=doctor_user)
    dept = Department.objects.create(name="Cardiology", slug="cardio")
    DoctorDepartment.objects.create(doctor=profile, department=dept)
    with pytest.raises(IntegrityError):
        DoctorDepartment.objects.create(doctor=profile, department=dept)


@pytest.mark.xfail(reason="set_doctor_departments lands in Task 7", strict=False)
@pytest.mark.django_db
def test_doctor_has_at_most_one_primary_department(doctor_user, db):
    from content.models import DoctorDepartment
    from content.services import set_doctor_departments  # imported lazily

    profile = DoctorProfile.objects.create(user=doctor_user)
    d1 = Department.objects.create(name="A", slug="a")
    d2 = Department.objects.create(name="B", slug="b")
    DoctorDepartment.objects.create(doctor=profile, department=d1, is_primary=True)
    # Second primary on same doctor must be rejected by service layer
    with pytest.raises(ValueError):
        set_doctor_departments(
            profile,
            assignments=[
                {"department_id": d1.id, "is_primary": True},
                {"department_id": d2.id, "is_primary": True},
            ],
        )
