from __future__ import annotations

from django.conf import settings
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    summary = models.CharField(max_length=200, blank=True)
    description_html = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="departments/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self) -> str:
        return self.name


class DoctorProfile(models.Model):
    class DraftStatus(models.TextChoices):
        NONE = "none", "None"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )
    title = models.CharField(max_length=80, blank=True)
    specialty = models.CharField(max_length=200, blank=True)
    bio_published_html = models.TextField(blank=True)
    bio_draft_html = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="doctors/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    draft_status = models.CharField(
        max_length=12, choices=DraftStatus.choices, default=DraftStatus.NONE
    )
    draft_submitted_at = models.DateTimeField(null=True, blank=True)
    draft_reviewed_at = models.DateTimeField(null=True, blank=True)
    draft_review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "user__name", "user__username")

    def __str__(self) -> str:
        return f"DoctorProfile<{self.user.username}>"


class DoctorDepartment(models.Model):
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="department_links"
    )
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="doctor_links"
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "department"],
                name="uniq_doctor_department_pair",
            ),
        ]
