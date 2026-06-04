from __future__ import annotations

import re
from collections.abc import Iterable
from typing import TypedDict
from urllib.parse import urlparse

import bleach
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from content.models import Department, DoctorDepartment, DoctorProfile

ALLOWED_TAGS = (
    "p",
    "h1",
    "h2",
    "h3",
    "strong",
    "em",
    "u",
    "ul",
    "ol",
    "li",
    "blockquote",
    "a",
    "img",
    "br",
)

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
}

ALLOWED_PROTOCOLS = ("http", "https")


def _image_src_allowed(tag: str, name: str, value: str, allowed_prefix: str) -> bool:
    if name != "src":
        return name in {"alt", "title"}
    if value.startswith("/media/"):
        return True
    if allowed_prefix:
        return value.startswith(allowed_prefix)
    return False


def sanitize_html(html: str, *, allowed_image_prefix: str | None = None) -> str:
    """Sanitize rich-text HTML to a strict allowlist.

    Allowed image `src` must either start with `/media/` (same-origin relative)
    or with `allowed_image_prefix` (typically the MinIO public endpoint).
    Defaults to the configured `MINIO_PUBLIC_ENDPOINT` if not passed.
    """
    if allowed_image_prefix is None:
        allowed_image_prefix = getattr(settings, "MINIO_PUBLIC_ENDPOINT", "") or ""
        if allowed_image_prefix and not allowed_image_prefix.endswith("/"):
            allowed_image_prefix = allowed_image_prefix + "/"

    # Pre-process: remove script and style tags entirely (including their content)
    # This ensures malicious script content doesn't leak even as text
    html = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>", "", html or "", flags=re.IGNORECASE | re.DOTALL
    )

    def attr_filter(tag: str, name: str, value: str) -> bool:
        if tag == "img":
            return _image_src_allowed(tag, name, value, allowed_image_prefix)
        if tag == "a" and name == "href":
            scheme = urlparse(value).scheme.lower()
            return scheme in ALLOWED_PROTOCOLS
        return name in ALLOWED_ATTRIBUTES.get(tag, [])

    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=attr_filter,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )
    # Post-process: remove img tags that lost their src attribute
    # (which means src was not allowed or missing)
    cleaned = re.sub(r"<img(?![^>]*\ssrc=)", "", cleaned)
    return cleaned


class DraftConflictError(Exception):
    """Raised when a draft transition is attempted from an incompatible state."""


class AssignmentDict(TypedDict):
    department_id: int
    is_primary: bool


def submit_doctor_review(profile: DoctorProfile) -> DoctorProfile:
    if profile.draft_status != DoctorProfile.DraftStatus.NONE:
        raise DraftConflictError(f"cannot submit when status is {profile.draft_status}")
    profile.draft_status = DoctorProfile.DraftStatus.PENDING
    profile.draft_submitted_at = timezone.now()
    profile.draft_review_note = ""
    profile.save(
        update_fields=[
            "draft_status",
            "draft_submitted_at",
            "draft_review_note",
            "updated_at",
        ]
    )
    return profile


def approve_doctor_profile(profile: DoctorProfile) -> DoctorProfile:
    if profile.draft_status != DoctorProfile.DraftStatus.PENDING:
        raise DraftConflictError(f"cannot approve when status is {profile.draft_status}")
    profile.bio_published_html = profile.bio_draft_html
    profile.draft_status = DoctorProfile.DraftStatus.APPROVED
    # Approving publishes the profile so it surfaces on the public portal
    # (the portal queries filter on is_published=True).
    profile.is_published = True
    profile.draft_reviewed_at = timezone.now()
    profile.draft_review_note = ""
    profile.save(
        update_fields=[
            "bio_published_html",
            "draft_status",
            "is_published",
            "draft_reviewed_at",
            "draft_review_note",
            "updated_at",
        ]
    )
    return profile


def reject_doctor_profile(profile: DoctorProfile, *, note: str) -> DoctorProfile:
    if profile.draft_status != DoctorProfile.DraftStatus.PENDING:
        raise DraftConflictError(f"cannot reject when status is {profile.draft_status}")
    profile.draft_status = DoctorProfile.DraftStatus.REJECTED
    profile.draft_review_note = note
    profile.draft_reviewed_at = timezone.now()
    profile.save(
        update_fields=[
            "draft_status",
            "draft_review_note",
            "draft_reviewed_at",
            "updated_at",
        ]
    )
    return profile


EDITABLE_DRAFT_FIELDS = {"title", "specialty", "bio_draft_html", "cover_image"}


def save_doctor_draft(profile: DoctorProfile, *, fields: dict) -> DoctorProfile:
    if profile.draft_status == DoctorProfile.DraftStatus.PENDING:
        raise DraftConflictError("draft is locked while review is pending")
    if "bio_draft_html" in fields:
        fields["bio_draft_html"] = sanitize_html(fields["bio_draft_html"])
    updated_keys: list[str] = []
    for key, value in fields.items():
        if key not in EDITABLE_DRAFT_FIELDS:
            continue
        setattr(profile, key, value)
        updated_keys.append(key)
    if profile.draft_status in (
        DoctorProfile.DraftStatus.APPROVED,
        DoctorProfile.DraftStatus.REJECTED,
    ):
        profile.draft_status = DoctorProfile.DraftStatus.NONE
        updated_keys.append("draft_status")
    updated_keys.append("updated_at")
    profile.save(update_fields=updated_keys)
    return profile


@transaction.atomic
def set_doctor_departments(
    profile: DoctorProfile, *, assignments: Iterable[AssignmentDict]
) -> None:
    items = list(assignments)
    primaries = [a for a in items if a.get("is_primary")]
    if len(primaries) > 1:
        raise ValueError("at most one is_primary=True per doctor")

    dept_ids = [a["department_id"] for a in items]
    if len(dept_ids) != len(set(dept_ids)):
        raise ValueError("duplicate department in assignments")

    existing = {dep.id for dep in Department.objects.filter(id__in=dept_ids)}
    missing = set(dept_ids) - existing
    if missing:
        raise ValueError(f"unknown department ids: {sorted(missing)}")

    DoctorDepartment.objects.filter(doctor=profile).delete()
    DoctorDepartment.objects.bulk_create(
        [
            DoctorDepartment(
                doctor=profile,
                department_id=a["department_id"],
                is_primary=bool(a.get("is_primary", False)),
            )
            for a in items
        ]
    )
