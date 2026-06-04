from __future__ import annotations

import pytest

from content.models import Department, DoctorDepartment, DoctorProfile
from content.services import (
    DraftConflictError,
    approve_doctor_profile,
    reject_doctor_profile,
    save_doctor_draft,
    set_doctor_departments,
    submit_doctor_review,
)


@pytest.mark.django_db
def test_submit_from_none_to_pending(doctor_user):
    p = DoctorProfile.objects.create(user=doctor_user, bio_draft_html="<p>x</p>")
    submit_doctor_review(p)
    p.refresh_from_db()
    assert p.draft_status == DoctorProfile.DraftStatus.PENDING
    assert p.draft_submitted_at is not None


@pytest.mark.django_db
def test_submit_while_pending_raises(doctor_user):
    p = DoctorProfile.objects.create(
        user=doctor_user, draft_status=DoctorProfile.DraftStatus.PENDING
    )
    with pytest.raises(DraftConflictError):
        submit_doctor_review(p)


@pytest.mark.django_db
def test_approve_copies_draft_to_published(doctor_user):
    p = DoctorProfile.objects.create(
        user=doctor_user,
        bio_draft_html="<p>new</p>",
        bio_published_html="<p>old</p>",
        draft_status=DoctorProfile.DraftStatus.PENDING,
    )
    approve_doctor_profile(p)
    p.refresh_from_db()
    assert p.bio_published_html == "<p>new</p>"
    assert p.draft_status == DoctorProfile.DraftStatus.APPROVED
    assert p.draft_reviewed_at is not None
    # approving a draft must publish the profile so it appears on the public portal
    assert p.is_published is True


@pytest.mark.django_db
def test_reject_records_note(doctor_user):
    p = DoctorProfile.objects.create(
        user=doctor_user, draft_status=DoctorProfile.DraftStatus.PENDING
    )
    reject_doctor_profile(p, note="too short")
    p.refresh_from_db()
    assert p.draft_status == DoctorProfile.DraftStatus.REJECTED
    assert p.draft_review_note == "too short"


@pytest.mark.django_db
def test_approve_only_from_pending(doctor_user):
    p = DoctorProfile.objects.create(user=doctor_user)
    with pytest.raises(DraftConflictError):
        approve_doctor_profile(p)


@pytest.mark.django_db
def test_save_draft_demotes_approved_to_none(doctor_user):
    p = DoctorProfile.objects.create(
        user=doctor_user, draft_status=DoctorProfile.DraftStatus.APPROVED
    )
    save_doctor_draft(p, fields={"bio_draft_html": "<p>edit</p>"})
    p.refresh_from_db()
    assert p.draft_status == DoctorProfile.DraftStatus.NONE
    assert p.bio_draft_html == "<p>edit</p>"


@pytest.mark.django_db
def test_save_draft_during_pending_raises(doctor_user):
    p = DoctorProfile.objects.create(
        user=doctor_user, draft_status=DoctorProfile.DraftStatus.PENDING
    )
    with pytest.raises(DraftConflictError):
        save_doctor_draft(p, fields={"bio_draft_html": "<p>x</p>"})


@pytest.mark.django_db
def test_set_doctor_departments_replaces_full_set(doctor_user):
    p = DoctorProfile.objects.create(user=doctor_user)
    d1 = Department.objects.create(name="A", slug="a")
    d2 = Department.objects.create(name="B", slug="b")
    d3 = Department.objects.create(name="C", slug="c")
    DoctorDepartment.objects.create(doctor=p, department=d1, is_primary=True)

    set_doctor_departments(
        p,
        assignments=[
            {"department_id": d2.id, "is_primary": True},
            {"department_id": d3.id, "is_primary": False},
        ],
    )
    links = list(p.department_links.order_by("department_id").values("department_id", "is_primary"))
    assert links == [
        {"department_id": d2.id, "is_primary": True},
        {"department_id": d3.id, "is_primary": False},
    ]


@pytest.mark.django_db
def test_set_doctor_departments_rejects_multiple_primary(doctor_user):
    p = DoctorProfile.objects.create(user=doctor_user)
    d1 = Department.objects.create(name="A", slug="a")
    d2 = Department.objects.create(name="B", slug="b")
    with pytest.raises(ValueError):
        set_doctor_departments(
            p,
            assignments=[
                {"department_id": d1.id, "is_primary": True},
                {"department_id": d2.id, "is_primary": True},
            ],
        )
