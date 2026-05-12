# Departments & Doctor Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add public-facing department and doctor introduction modules (rich text + images), a doctor draft → admin review workflow, a MinIO-backed media pipeline, public `/portal/*` pages, and a department carousel on the login page.

**Architecture:** New `content` Django app holds `Department`, `DoctorProfile` (1:1 to `User`), and `DoctorDepartment` (M2M join). MinIO is added as a service in `docker-compose`, accessed via `django-storages` S3 backend. Doctor introductions live as `bio_draft_html` / `bio_published_html` pairs with a 4-state machine (`none` / `pending` / `approved` / `rejected`). Frontend gets a new `features/content` module with portal, admin, and doctor pages plus a shared `RichTextEditor.vue` wrapping Wangeditor 5.

**Tech Stack:**
- Backend: Django 4.2, DRF, `django-storages[s3]`, `boto3`, `bleach`, `Pillow`
- Frontend: Vue 3, TypeScript, Element Plus, `@wangeditor/editor-for-vue@next`
- Storage: MinIO (S3-compatible) running in docker-compose
- Tests: pytest + factory_boy + pytest-django (backend), vitest + @vue/test-utils (frontend)

**Reference spec:** `docs/superpowers/specs/2026-05-12-departments-and-doctor-profiles-design.md`

---

## File Structure

### Backend — new files

```
backend/content/
├── __init__.py
├── apps.py
├── models.py                       # Department, DoctorProfile, DoctorDepartment
├── admin.py                        # Django admin registration
├── permissions.py                  # IsAdmin, IsDoctorSelf
├── throttles.py                    # PortalAnonThrottle
├── serializers.py                  # all serializers
├── services.py                     # sanitize_html, state machine, assignment replace
├── views_admin.py                  # admin endpoints
├── views_doctor.py                 # doctor self endpoints
├── views_portal.py                 # public endpoints
├── views_media.py                  # /api/media/upload/
├── urls.py
└── migrations/
    └── 0001_initial.py             # auto-generated

backend/sitemap_views.py            # /sitemap.xml view (project root, not in an app)

backend/tests/content/
├── __init__.py
├── test_models.py
├── test_services_sanitize.py
├── test_services_state_machine.py
├── test_api_portal.py
├── test_api_admin.py
├── test_api_doctor.py
└── test_api_media.py
```

### Backend — modified files

- `backend/config/settings.py` — add `content` to `INSTALLED_APPS`, add `STORAGES`/MinIO config, throttle class, REST_FRAMEWORK throttle rates
- `backend/config/urls.py` — include content URLs + sitemap
- `backend/requirements.txt` — add `django-storages[s3]==1.14.4`, `boto3==1.35.0`, `bleach==6.2.0`, `Pillow==11.0.0`
- `backend/scripts/bootstrap-backend.sh` — add MinIO bucket bootstrap step
- `backend/tests/factories.py` — add `DepartmentFactory`, `DoctorProfileFactory`
- `backend/pyproject.toml` — add `content` to coverage source

### Infra — modified files

- `docker-compose.yml` — add `minio` service + named volume
- `docker-compose.2c4g.yml` — MinIO memory limit
- `.env.example` — `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET`, `MINIO_ENDPOINT`, `MINIO_PUBLIC_ENDPOINT`

### Frontend — new files

```
frontend/src/features/content/
├── index.ts
├── types.ts
├── api/
│   ├── departments.ts
│   ├── doctor-profiles.ts
│   ├── media-upload.ts
│   └── index.ts
├── components/
│   ├── DepartmentCard.vue
│   ├── DepartmentCarousel.vue
│   ├── DoctorCard.vue
│   └── PublishStatusBadge.vue
├── composables/
│   ├── usePortalDepartments.ts
│   └── useDraftReview.ts
├── pages/
│   ├── portal/
│   │   ├── PortalDepartmentList.vue
│   │   ├── PortalDepartmentDetail.vue
│   │   ├── PortalDoctorList.vue
│   │   └── PortalDoctorDetail.vue
│   ├── admin/
│   │   ├── AdminDepartmentList.vue
│   │   ├── AdminDepartmentEdit.vue
│   │   ├── AdminDoctorProfileList.vue
│   │   ├── AdminDoctorProfileEdit.vue
│   │   └── AdminPendingReviews.vue
│   └── doctor/
│       └── DoctorMyProfile.vue
└── stores/
    └── content-store.ts

frontend/src/shared/components/
└── RichTextEditor.vue

frontend/src/features/content/__tests__/
├── DepartmentCarousel.spec.ts
├── DepartmentCard.spec.ts
├── PublishStatusBadge.spec.ts
└── usePortalDepartments.spec.ts
```

### Frontend — modified files

- `frontend/src/router/index.ts` — register `/portal/*`, `/admin/departments`, `/admin/reviews`, `/admin/doctor-profiles`, `/doctor/profile` (and adjust guard for unauthenticated portal access)
- `frontend/src/views/LoginPage.vue` — embed `<DepartmentCarousel />` and CTA buttons in left panel
- `frontend/src/App.vue` — extend `navItems` with content management items per role
- `frontend/package.json` — add `@wangeditor/editor`, `@wangeditor/editor-for-vue@next`

### Docs — modified files

- `docs/internal/PRODUCT_OVERVIEW.md` — add §3.7 Content Portal; remove from §10
- `README.md` — architecture mention, env vars
- `backend/README.md` — module map adds `content`
- `frontend/README.md` — feature list adds `content`

---

## Implementation Phases

The plan is grouped into 7 phases. Each task ends with a commit. Phase boundaries are natural review points — pause and verify before continuing to the next phase.

- **Phase 1 — Backend dependencies & app skeleton** (Tasks 1–2)
- **Phase 2 — Data layer** (Tasks 3–5)
- **Phase 3 — Service layer** (Tasks 6–7)
- **Phase 4 — API layer** (Tasks 8–12)
- **Phase 5 — Infra: MinIO** (Tasks 13–14)
- **Phase 6 — Frontend foundation** (Tasks 15–17)
- **Phase 7 — Frontend pages & integration** (Tasks 18–22)
- **Wrap-up** (Task 23)

---

## Phase 1 — Backend dependencies & app skeleton

### Task 1: Add Python dependencies

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Append new pinned dependencies**

Edit `backend/requirements.txt` to append (after `gunicorn==22.0.0`):

```
django-storages[s3]==1.14.4
boto3==1.35.99
bleach==6.2.0
Pillow==11.0.0
```

- [ ] **Step 2: Reinstall inside the running backend container or local venv**

If using docker compose:

```bash
docker compose exec backend pip install -r requirements.txt
```

If using local venv:

```bash
cd backend && pip install -r requirements.txt
```

- [ ] **Step 3: Verify imports work**

```bash
cd backend && python -c "import boto3, bleach, storages, PIL; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "Add django-storages, boto3, bleach, Pillow for content module"
```

---

### Task 2: Scaffold the `content` Django app

**Files:**
- Create: `backend/content/__init__.py` (empty)
- Create: `backend/content/apps.py`
- Create: `backend/content/models.py` (empty placeholder; populated in Task 3)
- Create: `backend/content/urls.py` (empty placeholder; populated in Task 12)
- Create: `backend/tests/content/__init__.py` (empty)
- Modify: `backend/config/settings.py`
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Create the app package**

Create `backend/content/__init__.py`:

```python
```

(Empty file. Required for Python package recognition.)

Create `backend/content/apps.py`:

```python
from django.apps import AppConfig


class ContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "content"
```

Create `backend/content/models.py`:

```python
# Models live here. Populated in Task 3.
```

Create `backend/content/urls.py`:

```python
# URL conf populated in Task 12.
from django.urls import path

urlpatterns: list = []
```

Create `backend/tests/content/__init__.py`:

```python
```

- [ ] **Step 2: Register the app in settings**

Edit `backend/config/settings.py`. Locate `INSTALLED_APPS = [...]` and add `"content"` after `"appointments"`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "users",
    "appointments",
    "content",
]
```

- [ ] **Step 3: Add coverage source**

Edit `backend/pyproject.toml`. Locate `[tool.coverage.run]` and update:

```toml
[tool.coverage.run]
source = ["users", "appointments", "content"]
branch = true
```

- [ ] **Step 4: Verify Django picks up the app**

```bash
cd backend && python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 5: Commit**

```bash
git add backend/content/ backend/tests/content/ backend/config/settings.py backend/pyproject.toml
git commit -m "Scaffold content Django app and register in settings"
```

---

## Phase 2 — Data layer

### Task 3: `Department` model + first migration

**Files:**
- Modify: `backend/content/models.py`
- Create: `backend/content/migrations/__init__.py` (empty)
- Create: `backend/content/migrations/0001_initial.py` (auto-generated)
- Create: `backend/tests/content/test_models.py`
- Modify: `backend/tests/factories.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/content/test_models.py`:

```python
from __future__ import annotations

import pytest
from django.db import IntegrityError

from content.models import Department


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
```

- [ ] **Step 2: Run the test and watch it fail**

```bash
cd backend && pytest tests/content/test_models.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` for `content.models.Department`.

- [ ] **Step 3: Implement the model**

Replace `backend/content/models.py` with:

```python
from __future__ import annotations

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
```

- [ ] **Step 4: Generate the migration**

```bash
mkdir -p backend/content/migrations
touch backend/content/migrations/__init__.py
cd backend && python manage.py makemigrations content
```

Expected output mentions `Create model Department`.

- [ ] **Step 5: Run the test again**

```bash
cd backend && pytest tests/content/test_models.py -v
```

Expected: both tests PASS.

- [ ] **Step 6: Add a Department factory**

Edit `backend/tests/factories.py`. Append:

```python
from content.models import Department


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Department

    name = factory.Sequence(lambda n: f"Department {n}")
    slug = factory.Sequence(lambda n: f"department-{n}")
    summary = "Sample summary"
    description_html = "<p>Sample description</p>"
    is_published = True
    display_order = 0
```

(If the file does not import `factory`, look for the existing `import factory` at the top and add this block near the other factories.)

- [ ] **Step 7: Commit**

```bash
git add backend/content/models.py backend/content/migrations/ backend/tests/content/ backend/tests/factories.py
git commit -m "Add Department model with slug uniqueness and ordering"
```

---

### Task 4: `DoctorProfile` model

**Files:**
- Modify: `backend/content/models.py`
- Modify: `backend/tests/content/test_models.py`
- Modify: `backend/tests/factories.py`

- [ ] **Step 1: Write failing tests**

Append to `backend/tests/content/test_models.py`:

```python
from content.models import DoctorProfile


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
```

- [ ] **Step 2: Run the tests to confirm failure**

```bash
cd backend && pytest tests/content/test_models.py -v
```

Expected: `ImportError` on `DoctorProfile`.

- [ ] **Step 3: Add the model**

Append to `backend/content/models.py`:

```python
from django.conf import settings


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
```

- [ ] **Step 4: Generate migration**

```bash
cd backend && python manage.py makemigrations content
```

Expected: a `0002_doctorprofile.py` is created (or merged into `0001_initial.py` if the model file is regenerated — either is fine).

- [ ] **Step 5: Run tests to confirm pass**

```bash
cd backend && pytest tests/content/test_models.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Add the factory**

Append to `backend/tests/factories.py`:

```python
from content.models import DoctorProfile


class DoctorProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DoctorProfile

    user = factory.SubFactory(UserFactory, role="doctor")
    title = "Consultant"
    specialty = "General"
    bio_published_html = "<p>Bio</p>"
    is_published = True
```

- [ ] **Step 7: Commit**

```bash
git add backend/content/models.py backend/content/migrations/ backend/tests/content/test_models.py backend/tests/factories.py
git commit -m "Add DoctorProfile 1:1 to User with draft workflow fields"
```

---

### Task 5: `DoctorDepartment` join table with uniqueness constraints

**Files:**
- Modify: `backend/content/models.py`
- Modify: `backend/content/migrations/` (new auto-generated migration)
- Modify: `backend/tests/content/test_models.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/content/test_models.py`:

```python
from content.models import DoctorDepartment


@pytest.mark.django_db
def test_doctor_department_pair_is_unique(doctor_user):
    profile = DoctorProfile.objects.create(user=doctor_user)
    dept = Department.objects.create(name="Cardiology", slug="cardio")
    DoctorDepartment.objects.create(doctor=profile, department=dept)
    with pytest.raises(IntegrityError):
        DoctorDepartment.objects.create(doctor=profile, department=dept)


@pytest.mark.django_db
def test_doctor_has_at_most_one_primary_department(doctor_user, db):
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd backend && pytest tests/content/test_models.py::test_doctor_department_pair_is_unique -v
```

Expected: `ImportError` for `DoctorDepartment`.

- [ ] **Step 3: Add the join model**

Append to `backend/content/models.py`:

```python
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
```

> Note: SQLite (local dev) does not support partial unique indexes well, so the "at most one is_primary=True per doctor" rule is enforced in the service layer (Task 7), not via a DB constraint. The pair-uniqueness constraint above runs on both SQLite and Postgres.

- [ ] **Step 4: Generate the migration**

```bash
cd backend && python manage.py makemigrations content
```

- [ ] **Step 5: Run the first test to confirm pass**

```bash
cd backend && pytest tests/content/test_models.py::test_doctor_department_pair_is_unique -v
```

Expected: PASS. (The second test will still fail until Task 7 adds `set_doctor_departments`.)

- [ ] **Step 6: Commit**

```bash
git add backend/content/models.py backend/content/migrations/ backend/tests/content/test_models.py
git commit -m "Add DoctorDepartment join with pair uniqueness"
```

---

## Phase 3 — Service layer

### Task 6: HTML sanitization

**Files:**
- Create: `backend/content/services.py` (sanitize section)
- Create: `backend/tests/content/test_services_sanitize.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/content/test_services_sanitize.py`:

```python
from __future__ import annotations

from content.services import sanitize_html


def test_strips_script_tags():
    out = sanitize_html("<p>hi</p><script>alert(1)</script>")
    assert "<script>" not in out
    assert "alert(1)" not in out
    assert "<p>hi</p>" in out


def test_strips_event_handlers():
    out = sanitize_html('<a href="https://x" onclick="bad()">link</a>')
    assert "onclick" not in out
    assert 'href="https://x"' in out


def test_strips_inline_styles():
    out = sanitize_html('<p style="color:red">x</p>')
    assert "style" not in out


def test_keeps_allowed_tags():
    src = (
        "<h1>T</h1><h2>S</h2><h3>U</h3>"
        "<p><strong>b</strong><em>i</em><u>u</u></p>"
        "<ul><li>a</li></ul><ol><li>1</li></ol>"
        "<blockquote>q</blockquote><br>"
    )
    out = sanitize_html(src)
    for tag in ("<h1>", "<h2>", "<h3>", "<strong>", "<em>", "<u>", "<ul>", "<ol>", "<li>", "<blockquote>", "<br"):
        assert tag in out


def test_blocks_external_image_sources():
    out = sanitize_html(
        '<p>x</p><img src="https://evil.example.com/x.png">',
        allowed_image_prefix="http://localhost:9000/",
    )
    assert "<img" not in out


def test_keeps_platform_image_sources():
    out = sanitize_html(
        '<img src="http://localhost:9000/clinic-media/media/inline/a.png" alt="a">',
        allowed_image_prefix="http://localhost:9000/",
    )
    assert "<img" in out
    assert 'src="http://localhost:9000/clinic-media/media/inline/a.png"' in out


def test_keeps_relative_media_paths():
    out = sanitize_html(
        '<img src="/media/inline/a.png">',
        allowed_image_prefix="http://localhost:9000/",
    )
    assert "<img" in out
```

- [ ] **Step 2: Run tests and confirm failure**

```bash
cd backend && pytest tests/content/test_services_sanitize.py -v
```

Expected: ImportError for `content.services.sanitize_html`.

- [ ] **Step 3: Implement `sanitize_html`**

Create `backend/content/services.py`:

```python
from __future__ import annotations

from urllib.parse import urlparse

import bleach
from django.conf import settings

ALLOWED_TAGS = (
    "p", "h1", "h2", "h3", "strong", "em", "u",
    "ul", "ol", "li", "blockquote", "a", "img", "br",
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
    return value.startswith(allowed_prefix)


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

    def attr_filter(tag: str, name: str, value: str) -> bool:
        if tag == "img":
            return _image_src_allowed(tag, name, value, allowed_image_prefix)
        if tag == "a" and name == "href":
            scheme = urlparse(value).scheme.lower()
            return scheme in ALLOWED_PROTOCOLS
        return name in ALLOWED_ATTRIBUTES.get(tag, [])

    cleaned = bleach.clean(
        html or "",
        tags=ALLOWED_TAGS,
        attributes=attr_filter,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )
    return cleaned
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
cd backend && pytest tests/content/test_services_sanitize.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/content/services.py backend/tests/content/test_services_sanitize.py
git commit -m "Add sanitize_html with strict tag/attribute allowlist"
```

---

### Task 7: Draft-state machine and department assignment

**Files:**
- Modify: `backend/content/services.py`
- Create: `backend/tests/content/test_services_state_machine.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/content/test_services_state_machine.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd backend && pytest tests/content/test_services_state_machine.py -v
```

Expected: ImportError for the service functions.

- [ ] **Step 3: Implement state machine and assignment service**

Append to `backend/content/services.py`:

```python
from typing import Iterable, TypedDict

from django.db import transaction
from django.utils import timezone

from content.models import Department, DoctorDepartment, DoctorProfile


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
    profile.save(update_fields=["draft_status", "draft_submitted_at", "draft_review_note", "updated_at"])
    return profile


def approve_doctor_profile(profile: DoctorProfile) -> DoctorProfile:
    if profile.draft_status != DoctorProfile.DraftStatus.PENDING:
        raise DraftConflictError(f"cannot approve when status is {profile.draft_status}")
    profile.bio_published_html = profile.bio_draft_html
    profile.draft_status = DoctorProfile.DraftStatus.APPROVED
    profile.draft_reviewed_at = timezone.now()
    profile.draft_review_note = ""
    profile.save(update_fields=[
        "bio_published_html", "draft_status", "draft_reviewed_at",
        "draft_review_note", "updated_at",
    ])
    return profile


def reject_doctor_profile(profile: DoctorProfile, *, note: str) -> DoctorProfile:
    if profile.draft_status != DoctorProfile.DraftStatus.PENDING:
        raise DraftConflictError(f"cannot reject when status is {profile.draft_status}")
    profile.draft_status = DoctorProfile.DraftStatus.REJECTED
    profile.draft_review_note = note
    profile.draft_reviewed_at = timezone.now()
    profile.save(update_fields=[
        "draft_status", "draft_review_note", "draft_reviewed_at", "updated_at",
    ])
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
    if profile.draft_status in (DoctorProfile.DraftStatus.APPROVED, DoctorProfile.DraftStatus.REJECTED):
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
```

- [ ] **Step 4: Run state-machine tests to confirm pass**

```bash
cd backend && pytest tests/content/test_services_state_machine.py tests/content/test_models.py -v
```

Expected: all PASS.

- [ ] **Step 5: Run ruff and black**

```bash
cd backend && ruff check . && black --check .
```

Expected: no errors. (If black wants to reformat, run `black .` and re-check.)

- [ ] **Step 6: Commit**

```bash
git add backend/content/services.py backend/tests/content/test_services_state_machine.py
git commit -m "Add doctor-profile state machine and department assignment service"
```

---

## Phase 4 — API layer

### Task 8: Permissions, throttle, serializers

**Files:**
- Create: `backend/content/permissions.py`
- Create: `backend/content/throttles.py`
- Create: `backend/content/serializers.py`
- Modify: `backend/config/settings.py` (REST_FRAMEWORK throttle config)

- [ ] **Step 1: Add permission classes**

Create `backend/content/permissions.py`:

```python
from __future__ import annotations

from rest_framework.permissions import BasePermission

from users.models import User


class IsAdminUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN
        )


class IsDoctorUser(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user and request.user.is_authenticated and request.user.role == User.Role.DOCTOR
        )
```

- [ ] **Step 2: Add throttle**

Create `backend/content/throttles.py`:

```python
from rest_framework.throttling import AnonRateThrottle


class PortalAnonThrottle(AnonRateThrottle):
    scope = "portal_anon"
```

- [ ] **Step 3: Wire throttle into settings**

Edit `backend/config/settings.py`. Locate the existing `REST_FRAMEWORK = {...}` block (or add one if absent). Ensure it contains:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_CLASSES": (),
    "DEFAULT_THROTTLE_RATES": {
        "portal_anon": "60/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
```

If the file already defines `REST_FRAMEWORK`, merge only the `DEFAULT_THROTTLE_CLASSES` and `DEFAULT_THROTTLE_RATES` keys — do not duplicate other settings.

- [ ] **Step 4: Add serializers**

Create `backend/content/serializers.py`:

```python
from __future__ import annotations

from rest_framework import serializers

from content.models import Department, DoctorDepartment, DoctorProfile


def _image_url(field) -> str | None:
    if not field:
        return None
    try:
        return field.url
    except Exception:
        return None


class DepartmentPortalSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ("id", "slug", "name", "summary", "cover_image_url", "display_order")

    def get_cover_image_url(self, obj):
        return _image_url(obj.cover_image)


class DepartmentDetailSerializer(DepartmentPortalSerializer):
    class Meta(DepartmentPortalSerializer.Meta):
        fields = DepartmentPortalSerializer.Meta.fields + ("description_html",)


class DepartmentAdminSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = (
            "id", "slug", "name", "summary", "description_html",
            "cover_image", "cover_image_url",
            "display_order", "is_published",
            "created_at", "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "cover_image_url")

    def get_cover_image_url(self, obj):
        return _image_url(obj.cover_image)

    def validate_description_html(self, value):
        from content.services import sanitize_html
        return sanitize_html(value)


class DoctorDepartmentLinkSerializer(serializers.Serializer):
    slug = serializers.CharField(source="department.slug", read_only=True)
    name = serializers.CharField(source="department.name", read_only=True)
    is_primary = serializers.BooleanField()


class DoctorPortalCardSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="user.id")
    name = serializers.CharField(source="user.name")
    title = serializers.CharField()
    specialty = serializers.CharField()
    cover_image_url = serializers.SerializerMethodField()
    departments = DoctorDepartmentLinkSerializer(many=True, source="department_links")

    def get_cover_image_url(self, obj):
        return _image_url(obj.cover_image)


class DoctorPortalDetailSerializer(DoctorPortalCardSerializer):
    bio_published_html = serializers.CharField()


class DoctorProfileSelfSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    departments = DoctorDepartmentLinkSerializer(many=True, source="department_links", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = (
            "title", "specialty",
            "bio_published_html", "bio_draft_html",
            "cover_image", "cover_image_url",
            "is_published",
            "draft_status", "draft_submitted_at", "draft_reviewed_at", "draft_review_note",
            "departments",
        )
        read_only_fields = (
            "bio_published_html", "is_published",
            "draft_status", "draft_submitted_at", "draft_reviewed_at", "draft_review_note",
            "departments", "cover_image_url",
        )

    def get_cover_image_url(self, obj):
        return _image_url(obj.cover_image)


class DoctorProfileAdminSerializer(DoctorProfileSelfSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)

    class Meta(DoctorProfileSelfSerializer.Meta):
        fields = ("user_id", "username", "name") + DoctorProfileSelfSerializer.Meta.fields


class DoctorAssignmentItemSerializer(serializers.Serializer):
    department_id = serializers.IntegerField()
    is_primary = serializers.BooleanField(default=False)


class RejectNoteSerializer(serializers.Serializer):
    note = serializers.CharField(required=True, allow_blank=False, max_length=2000)
```

- [ ] **Step 5: Run linter and verify imports**

```bash
cd backend && ruff check content/ && python -c "from content import serializers, permissions, throttles; print('ok')"
```

Expected: `ok`, no lint errors.

- [ ] **Step 6: Commit**

```bash
git add backend/content/permissions.py backend/content/throttles.py backend/content/serializers.py backend/config/settings.py
git commit -m "Add permissions, portal throttle, and serializers for content app"
```

---

### Task 9: Portal (public) endpoints

**Files:**
- Create: `backend/content/views_portal.py`
- Create: `backend/tests/content/test_api_portal.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/content/test_api_portal.py`:

```python
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
    return Department.objects.create(
        name="Hidden", slug="hidden", summary="x", is_published=False
    )


@pytest.fixture
def published_doctor(db, doctor_user, published_dept):
    p = DoctorProfile.objects.create(
        user=doctor_user, title="Dr.", specialty="Heart",
        bio_published_html="<p>hi</p>", is_published=True,
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
```

- [ ] **Step 2: Run the tests and confirm they fail**

```bash
cd backend && pytest tests/content/test_api_portal.py -v
```

Expected: 404 / route not found.

- [ ] **Step 3: Implement portal views**

Create `backend/content/views_portal.py`:

```python
from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Department, DoctorProfile
from content.serializers import (
    DepartmentDetailSerializer,
    DepartmentPortalSerializer,
    DoctorPortalCardSerializer,
    DoctorPortalDetailSerializer,
)
from content.throttles import PortalAnonThrottle


class PortalDepartmentListView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PortalAnonThrottle,)
    authentication_classes = ()

    def get(self, request):
        qs = Department.objects.filter(is_published=True).order_by("display_order", "name")
        limit = request.query_params.get("limit")
        if limit:
            try:
                qs = qs[: max(0, int(limit))]
            except ValueError:
                return Response(
                    {"error": {"code": "invalid_limit", "message": "limit must be integer"}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(DepartmentPortalSerializer(qs, many=True).data)


class PortalDepartmentDetailView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PortalAnonThrottle,)
    authentication_classes = ()

    def get(self, request, slug: str):
        try:
            dept = Department.objects.get(slug=slug, is_published=True)
        except Department.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "department not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        doctor_profiles = (
            DoctorProfile.objects.filter(
                is_published=True,
                department_links__department_id=dept.id,
            )
            .select_related("user")
            .prefetch_related("department_links__department")
            .order_by("display_order")
            .distinct()
        )
        return Response({
            "department": DepartmentDetailSerializer(dept).data,
            "doctors": DoctorPortalCardSerializer(doctor_profiles, many=True).data,
        })


class PortalDoctorListView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PortalAnonThrottle,)
    authentication_classes = ()

    def get(self, request):
        qs = (
            DoctorProfile.objects.filter(is_published=True)
            .select_related("user")
            .prefetch_related("department_links__department")
            .order_by("display_order")
        )
        slug = request.query_params.get("department")
        if slug:
            qs = qs.filter(department_links__department__slug=slug).distinct()
        return Response(DoctorPortalCardSerializer(qs, many=True).data)


class PortalDoctorDetailView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PortalAnonThrottle,)
    authentication_classes = ()

    def get(self, request, user_id: int):
        try:
            profile = (
                DoctorProfile.objects.select_related("user")
                .prefetch_related("department_links__department")
                .get(user_id=user_id, is_published=True)
            )
        except DoctorProfile.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "doctor not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(DoctorPortalDetailSerializer(profile).data)
```

- [ ] **Step 4: Wire URLs**

Replace `backend/content/urls.py` with:

```python
from django.urls import path

from content.views_portal import (
    PortalDepartmentDetailView,
    PortalDepartmentListView,
    PortalDoctorDetailView,
    PortalDoctorListView,
)

urlpatterns = [
    path("portal/departments/", PortalDepartmentListView.as_view()),
    path("portal/departments/<slug:slug>/", PortalDepartmentDetailView.as_view()),
    path("portal/doctors/", PortalDoctorListView.as_view()),
    path("portal/doctors/<int:user_id>/", PortalDoctorDetailView.as_view()),
]
```

Edit `backend/config/urls.py`. Append to `urlpatterns`:

```python
    path("api/", include("content.urls")),
```

- [ ] **Step 5: Run portal tests**

```bash
cd backend && pytest tests/content/test_api_portal.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/content/views_portal.py backend/content/urls.py backend/config/urls.py backend/tests/content/test_api_portal.py
git commit -m "Add public portal endpoints for departments and doctors"
```

---

### Task 10: Admin endpoints (CRUD + assignment + review)

**Files:**
- Create: `backend/content/views_admin.py`
- Modify: `backend/content/urls.py`
- Create: `backend/tests/content/test_api_admin.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/content/test_api_admin.py`:

```python
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
        [{"department_id": d1.id, "is_primary": True}, {"department_id": d2.id, "is_primary": False}],
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
        [{"department_id": d1.id, "is_primary": True}, {"department_id": d2.id, "is_primary": True}],
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


@pytest.mark.django_db
def test_admin_reject_requires_note(admin_client, doctor_user):
    DoctorProfile.objects.create(
        user=doctor_user, draft_status=DoctorProfile.DraftStatus.PENDING
    )
    resp = admin_client.post(f"/api/admin/content/doctor-profiles/{doctor_user.id}/reject/", {}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_admin_pending_review_list(admin_client, doctor_user):
    DoctorProfile.objects.create(
        user=doctor_user, draft_status=DoctorProfile.DraftStatus.PENDING
    )
    resp = admin_client.get("/api/admin/content/pending-reviews/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.django_db
def test_non_admin_cannot_access_admin_endpoints(authed_client):
    # authed_client is a doctor
    resp = authed_client.get("/api/admin/content/departments/")
    assert resp.status_code == 403
```

- [ ] **Step 2: Run tests and confirm failure**

```bash
cd backend && pytest tests/content/test_api_admin.py -v
```

Expected: 404 or import error.

- [ ] **Step 3: Implement admin views**

Create `backend/content/views_admin.py`:

```python
from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Department, DoctorProfile
from content.permissions import IsAdminUser
from content.serializers import (
    DepartmentAdminSerializer,
    DoctorAssignmentItemSerializer,
    DoctorProfileAdminSerializer,
    RejectNoteSerializer,
)
from content.services import (
    DraftConflictError,
    approve_doctor_profile,
    reject_doctor_profile,
    set_doctor_departments,
)


class AdminDepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by("display_order", "name")
    serializer_class = DepartmentAdminSerializer
    permission_classes = (IsAdminUser,)


class AdminDoctorProfileViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorProfileAdminSerializer
    permission_classes = (IsAdminUser,)
    lookup_field = "user_id"
    http_method_names = ("get", "put", "patch", "head", "options")

    def get_queryset(self):
        return (
            DoctorProfile.objects.select_related("user")
            .prefetch_related("department_links__department")
            .order_by("display_order")
        )


class AdminDoctorDepartmentsView(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request, user_id: int):
        ser = DoctorAssignmentItemSerializer(data=request.data, many=True)
        ser.is_valid(raise_exception=True)
        try:
            profile = DoctorProfile.objects.get(user_id=user_id)
        except DoctorProfile.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "doctor profile not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            set_doctor_departments(profile, assignments=ser.validated_data)
        except ValueError as exc:
            return Response(
                {"error": {"code": "invalid_assignment", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(DoctorProfileAdminSerializer(profile).data)


class AdminApproveDoctorView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request, user_id: int):
        profile = _get_profile_or_404(user_id)
        if isinstance(profile, Response):
            return profile
        try:
            approve_doctor_profile(profile)
        except DraftConflictError as exc:
            return Response(
                {"error": {"code": "draft_conflict", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DoctorProfileAdminSerializer(profile).data)


class AdminRejectDoctorView(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request, user_id: int):
        ser = RejectNoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        profile = _get_profile_or_404(user_id)
        if isinstance(profile, Response):
            return profile
        try:
            reject_doctor_profile(profile, note=ser.validated_data["note"])
        except DraftConflictError as exc:
            return Response(
                {"error": {"code": "draft_conflict", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DoctorProfileAdminSerializer(profile).data)


class AdminPendingReviewsView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        qs = (
            DoctorProfile.objects.filter(draft_status=DoctorProfile.DraftStatus.PENDING)
            .select_related("user")
            .order_by("draft_submitted_at")
        )
        return Response(DoctorProfileAdminSerializer(qs, many=True).data)


def _get_profile_or_404(user_id: int):
    try:
        return DoctorProfile.objects.get(user_id=user_id)
    except DoctorProfile.DoesNotExist:
        return Response(
            {"error": {"code": "not_found", "message": "doctor profile not found"}},
            status=status.HTTP_404_NOT_FOUND,
        )
```

- [ ] **Step 4: Update urls**

Replace `backend/content/urls.py` with:

```python
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from content.views_admin import (
    AdminApproveDoctorView,
    AdminDepartmentViewSet,
    AdminDoctorDepartmentsView,
    AdminDoctorProfileViewSet,
    AdminPendingReviewsView,
    AdminRejectDoctorView,
)
from content.views_portal import (
    PortalDepartmentDetailView,
    PortalDepartmentListView,
    PortalDoctorDetailView,
    PortalDoctorListView,
)

admin_router = SimpleRouter()
admin_router.register("departments", AdminDepartmentViewSet, basename="admin-department")
admin_router.register("doctor-profiles", AdminDoctorProfileViewSet, basename="admin-doctor-profile")

urlpatterns = [
    path("portal/departments/", PortalDepartmentListView.as_view()),
    path("portal/departments/<slug:slug>/", PortalDepartmentDetailView.as_view()),
    path("portal/doctors/", PortalDoctorListView.as_view()),
    path("portal/doctors/<int:user_id>/", PortalDoctorDetailView.as_view()),
    path("admin/content/", include(admin_router.urls)),
    path(
        "admin/content/doctor-profiles/<int:user_id>/departments/",
        AdminDoctorDepartmentsView.as_view(),
    ),
    path(
        "admin/content/doctor-profiles/<int:user_id>/approve/",
        AdminApproveDoctorView.as_view(),
    ),
    path(
        "admin/content/doctor-profiles/<int:user_id>/reject/",
        AdminRejectDoctorView.as_view(),
    ),
    path("admin/content/pending-reviews/", AdminPendingReviewsView.as_view()),
]
```

- [ ] **Step 5: Run admin tests**

```bash
cd backend && pytest tests/content/test_api_admin.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/content/views_admin.py backend/content/urls.py backend/tests/content/test_api_admin.py
git commit -m "Add admin endpoints for departments, profiles, assignments, and review"
```

---

### Task 11: Doctor self endpoints

**Files:**
- Create: `backend/content/views_doctor.py`
- Modify: `backend/content/urls.py`
- Create: `backend/tests/content/test_api_doctor.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/content/test_api_doctor.py`:

```python
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
    DoctorProfile.objects.get(user=doctor_user).draft_status == "pending"


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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
cd backend && pytest tests/content/test_api_doctor.py -v
```

Expected: 404 or import error.

- [ ] **Step 3: Implement doctor views**

Create `backend/content/views_doctor.py`:

```python
from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import DoctorProfile
from content.permissions import IsDoctorUser
from content.serializers import DoctorProfileSelfSerializer
from content.services import DraftConflictError, save_doctor_draft, submit_doctor_review


def _get_or_create(user) -> DoctorProfile:
    profile, _ = DoctorProfile.objects.get_or_create(user=user)
    return profile


class DoctorProfileMeView(APIView):
    permission_classes = (IsDoctorUser,)

    def get(self, request):
        profile = _get_or_create(request.user)
        return Response(DoctorProfileSelfSerializer(profile).data)

    def put(self, request):
        profile = _get_or_create(request.user)
        ser = DoctorProfileSelfSerializer(instance=profile, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            save_doctor_draft(profile, fields=dict(ser.validated_data))
        except DraftConflictError as exc:
            return Response(
                {"error": {"code": "draft_conflict", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DoctorProfileSelfSerializer(profile).data)


class DoctorSubmitReviewView(APIView):
    permission_classes = (IsDoctorUser,)

    def post(self, request):
        profile = _get_or_create(request.user)
        try:
            submit_doctor_review(profile)
        except DraftConflictError as exc:
            return Response(
                {"error": {"code": "draft_conflict", "message": str(exc)}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DoctorProfileSelfSerializer(profile).data)
```

- [ ] **Step 4: Wire URLs**

Edit `backend/content/urls.py`. Add to imports:

```python
from content.views_doctor import DoctorProfileMeView, DoctorSubmitReviewView
```

Add to `urlpatterns`:

```python
    path("doctor/content/profile/me/", DoctorProfileMeView.as_view()),
    path("doctor/content/profile/me/submit-review/", DoctorSubmitReviewView.as_view()),
```

- [ ] **Step 5: Run tests**

```bash
cd backend && pytest tests/content/test_api_doctor.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/content/views_doctor.py backend/content/urls.py backend/tests/content/test_api_doctor.py
git commit -m "Add doctor self-service endpoints for profile edit and submit-review"
```

---

### Task 12: Media upload endpoint

**Files:**
- Create: `backend/content/views_media.py`
- Modify: `backend/content/urls.py`
- Create: `backend/tests/content/test_api_media.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/content/test_api_media.py`:

```python
from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def _png_bytes(size_kb: int = 1) -> bytes:
    img = Image.new("RGB", (8, 8), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    payload = buf.getvalue()
    if size_kb > 1:
        payload = payload + b"\0" * (size_kb * 1024 - len(payload))
    return payload


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.mark.django_db
def test_upload_rejects_non_image(admin_client):
    f = SimpleUploadedFile("x.txt", b"hello", content_type="text/plain")
    resp = admin_client.post("/api/media/upload/", {"file": f}, format="multipart")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_upload_rejects_oversize(admin_client, settings):
    settings.MEDIA_UPLOAD_MAX_BYTES = 1024
    f = SimpleUploadedFile("big.png", _png_bytes(size_kb=2), content_type="image/png")
    resp = admin_client.post("/api/media/upload/", {"file": f}, format="multipart")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_upload_returns_url(admin_client):
    f = SimpleUploadedFile("ok.png", _png_bytes(), content_type="image/png")
    resp = admin_client.post("/api/media/upload/", {"file": f}, format="multipart")
    assert resp.status_code == 201, resp.content
    assert "url" in resp.json()


@pytest.mark.django_db
def test_upload_requires_admin_or_doctor(api_client, patient_user):
    api_client.force_authenticate(user=patient_user)
    f = SimpleUploadedFile("ok.png", _png_bytes(), content_type="image/png")
    resp = api_client.post("/api/media/upload/", {"file": f}, format="multipart")
    assert resp.status_code == 403
```

- [ ] **Step 2: Run tests and confirm failure**

```bash
cd backend && pytest tests/content/test_api_media.py -v
```

- [ ] **Step 3: Implement the view**

Create `backend/content/views_media.py`:

```python
from __future__ import annotations

import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
EXT_BY_CONTENT_TYPE = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
}
DEFAULT_MAX_BYTES = 5 * 1024 * 1024


class IsAdminOrDoctor(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and u.is_authenticated and u.role in (User.Role.ADMIN, User.Role.DOCTOR)
        )


class MediaUploadView(APIView):
    permission_classes = (IsAdminOrDoctor,)
    parser_classes = (MultiPartParser,)

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"error": {"code": "no_file", "message": "file field is required"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload.content_type not in ALLOWED_CONTENT_TYPES:
            return Response(
                {"error": {"code": "invalid_type", "message": "only PNG/JPG/WEBP allowed"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        max_bytes = getattr(settings, "MEDIA_UPLOAD_MAX_BYTES", DEFAULT_MAX_BYTES)
        if upload.size > max_bytes:
            return Response(
                {"error": {"code": "too_large", "message": f"max {max_bytes} bytes"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ext = EXT_BY_CONTENT_TYPE[upload.content_type]
        key = f"inline/{uuid.uuid4().hex}.{ext}"
        saved_path = default_storage.save(key, upload)
        url = default_storage.url(saved_path)
        return Response({"url": url}, status=status.HTTP_201_CREATED)
```

- [ ] **Step 4: Wire URL**

Edit `backend/content/urls.py`. Add to imports:

```python
from content.views_media import MediaUploadView
```

Add to `urlpatterns`:

```python
    path("media/upload/", MediaUploadView.as_view()),
```

- [ ] **Step 5: Run media tests**

```bash
cd backend && pytest tests/content/test_api_media.py -v
```

Expected: all 4 PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/content/views_media.py backend/content/urls.py backend/tests/content/test_api_media.py
git commit -m "Add /api/media/upload endpoint with type and size validation"
```

---

## Phase 5 — Infra: MinIO

### Task 13: docker-compose MinIO service and bucket bootstrap

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docker-compose.2c4g.yml`
- Modify: `.env.example`
- Modify: `backend/Dockerfile` (install `curl` for mc bootstrap, if not present)
- Modify: `backend/scripts/bootstrap-backend.sh`

- [ ] **Step 1: Add MinIO service to compose**

Edit `docker-compose.yml`. Add a new `minio` service entry, and add `minio_data` to the `volumes` section. Insert after the `db` service:

```yaml
  minio:
    image: docker-mirrors.alauda.cn/minio/minio:latest
    container_name: booking-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "sh", "-c", "wget -q -O- http://localhost:9000/minio/health/live || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 10
```

Update `backend` service to depend on MinIO and to expose its env vars:

```yaml
    depends_on:
      db:
        condition: service_healthy
      minio:
        condition: service_healthy
```

Update the bottom `volumes:` block:

```yaml
volumes:
  postgres_data:
  minio_data:
```

- [ ] **Step 2: Constrain MinIO memory in 2c4g override**

Edit `docker-compose.2c4g.yml`. Add a `minio` entry mirroring existing patterns:

```yaml
  minio:
    deploy:
      resources:
        limits:
          memory: 256M
```

(Use the same shape — `deploy.resources.limits.memory` or `mem_limit` — that the file already uses for `db`/`backend`. If the file uses `mem_limit`, write that instead. Read the existing file first to match style.)

- [ ] **Step 3: Add env variables to `.env.example`**

Append to `.env.example`:

```
# MinIO (S3-compatible object storage for portal media)
MINIO_ROOT_USER=clinic
MINIO_ROOT_PASSWORD=change-this-in-production
MINIO_BUCKET=clinic-media
MINIO_ENDPOINT=http://minio:9000
MINIO_PUBLIC_ENDPOINT=http://localhost:9000
```

- [ ] **Step 4: Ensure curl + mc binary available in backend image**

Read `backend/Dockerfile` first. If `curl` is not in the install list, add it. Append a step to download `mc` (MinIO Client):

```dockerfile
RUN curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc \
    && chmod +x /usr/local/bin/mc
```

(Match the file's existing layer style — keep the install with other apt/setup steps.)

- [ ] **Step 5: Extend bootstrap script with MinIO bucket setup**

Edit `backend/scripts/bootstrap-backend.sh`. Insert after the `[bootstrap] database is ready` block and before `migrate`:

```sh
if [ -n "${MINIO_ENDPOINT:-}" ] && [ -n "${MINIO_ROOT_USER:-}" ] && [ -n "${MINIO_ROOT_PASSWORD:-}" ]; then
  echo "[bootstrap] configuring MinIO bucket..."
  mc alias set local "$MINIO_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
  if ! mc ls "local/${MINIO_BUCKET:-clinic-media}" >/dev/null 2>&1; then
    mc mb "local/${MINIO_BUCKET:-clinic-media}"
  fi
  # Public read for media/ prefix only.
  cat > /tmp/policy.json <<'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::__BUCKET__/media/*"]
    }
  ]
}
POLICY
  sed -i "s/__BUCKET__/${MINIO_BUCKET:-clinic-media}/g" /tmp/policy.json
  mc anonymous set-json /tmp/policy.json "local/${MINIO_BUCKET:-clinic-media}" || true
  echo "[bootstrap] MinIO bucket ready"
fi
```

- [ ] **Step 6: Update Django settings to use S3 backend**

Edit `backend/config/settings.py`. Near where storage / STATIC settings live, add:

```python
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "clinic-media")
MEDIA_UPLOAD_MAX_BYTES = int(os.getenv("MEDIA_UPLOAD_MAX_BYTES", str(5 * 1024 * 1024)))

if MINIO_ENDPOINT:
    AWS_ACCESS_KEY_ID = os.getenv("MINIO_ROOT_USER")
    AWS_SECRET_ACCESS_KEY = os.getenv("MINIO_ROOT_PASSWORD")
    AWS_STORAGE_BUCKET_NAME = MINIO_BUCKET
    AWS_S3_ENDPOINT_URL = MINIO_ENDPOINT
    AWS_S3_ADDRESSING_STYLE = "path"
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_LOCATION = "media"
    # Public URLs go through MINIO_PUBLIC_ENDPOINT (browser-facing).
    public_host = MINIO_PUBLIC_ENDPOINT.replace("http://", "").replace("https://", "").rstrip("/")
    AWS_S3_CUSTOM_DOMAIN = f"{public_host}/{MINIO_BUCKET}" if public_host else None

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {},
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
```

(If `STORAGES` already exists in the file, replace its current value with the one above only when `MINIO_ENDPOINT` is set.)

- [ ] **Step 7: Run sanity check**

```bash
cd backend && python manage.py check
```

Expected: no system check errors.

- [ ] **Step 8: Commit**

```bash
git add docker-compose.yml docker-compose.2c4g.yml .env.example backend/Dockerfile backend/scripts/bootstrap-backend.sh backend/config/settings.py
git commit -m "Add MinIO service, bucket bootstrap, and S3 storage backend"
```

---

### Task 14: Smoke-test the stack end-to-end

**Files:**
- No code changes; verification only.

- [ ] **Step 1: Set MinIO env in `.env`**

Edit local `.env` (not committed) and populate the new MinIO variables matching `.env.example`. If `.env` is missing, copy from `.env.example` and edit secrets.

- [ ] **Step 2: Rebuild and start the stack**

```bash
sh ./cleanup-stack.sh
sh ./init-stack.sh
```

- [ ] **Step 3: Verify MinIO is healthy**

```bash
docker compose ps minio
curl -sf http://localhost:9000/minio/health/live && echo OK
```

Expected: status `healthy`; the curl returns 200.

- [ ] **Step 4: Verify bucket exists and is anonymously readable for `media/` prefix**

```bash
docker compose exec backend mc ls local/clinic-media/
docker compose exec backend mc anonymous list local/clinic-media/
```

Expected: bucket listed; anonymous policy showing read access on `media/*`.

- [ ] **Step 5: Smoke-test upload via the API**

Get an admin JWT, then:

```bash
echo "placeholder" > /tmp/x.png  # any small file
TOKEN=...  # obtain via /api/auth/login
curl -sf -X POST http://localhost:8000/api/media/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/x.png;type=image/png"
```

Expected: 201 with `{"url": "http://localhost:9000/clinic-media/media/inline/<uuid>.png"}`. Open the URL in a browser to confirm anonymous read works.

- [ ] **Step 6: No commit needed**

Manual verification only. If anything fails, fix the misconfiguration in the affected file from Task 13 and commit the fix as a follow-up.

---

## Phase 6 — Frontend foundation

### Task 15: Add Wangeditor dependency and `RichTextEditor.vue`

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/shared/components/RichTextEditor.vue`

- [ ] **Step 1: Install dependencies**

```bash
cd frontend && npm install @wangeditor/editor @wangeditor/editor-for-vue@next
```

This updates `package.json` and `package-lock.json`.

- [ ] **Step 2: Create the wrapper component**

Create `frontend/src/shared/components/RichTextEditor.vue`:

```vue
<script setup lang="ts">
import { onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import type { IDomEditor, IEditorConfig, IToolbarConfig } from '@wangeditor/editor'
import '@wangeditor/editor/dist/css/style.css'
import api from '@/shared/http/client'

interface Props {
  modelValue: string
  placeholder?: string
  disabled?: boolean
}
const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorRef = shallowRef<IDomEditor | null>(null)
const html = ref<string>(props.modelValue ?? '')

watch(
  () => props.modelValue,
  (v) => {
    if (v !== html.value) html.value = v ?? ''
  },
)

const toolbarConfig: Partial<IToolbarConfig> = {
  toolbarKeys: [
    'headerSelect',
    'bold', 'italic', 'underline',
    '|',
    'bulletedList', 'numberedList',
    'blockquote',
    '|',
    'insertLink', 'insertImage',
    '|',
    'clearStyle',
  ],
}

const editorConfig: Partial<IEditorConfig> = {
  placeholder: props.placeholder ?? 'Write something…',
  MENU_CONF: {
    uploadImage: {
      async customUpload(file: File, insertFn: (url: string) => void) {
        const data = new FormData()
        data.append('file', file)
        const res = await api.post<{ url: string }>('/media/upload/', data, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        insertFn(res.data.url)
      },
    },
  },
}

const handleCreated = (editor: IDomEditor) => {
  editorRef.value = editor
}

const handleChange = (editor: IDomEditor) => {
  const next = editor.getHtml()
  html.value = next
  emit('update:modelValue', next)
}

onBeforeUnmount(() => {
  editorRef.value?.destroy()
  editorRef.value = null
})
</script>

<template>
  <div class="rich-text-editor" :class="{ 'is-disabled': disabled }">
    <Toolbar :editor="editorRef" :default-config="toolbarConfig" mode="default" />
    <Editor
      v-model="html"
      :default-config="editorConfig"
      :mode="'default'"
      :default-html="modelValue"
      style="height: 320px; overflow-y: auto"
      @on-created="handleCreated"
      @on-change="handleChange"
    />
  </div>
</template>

<style scoped>
.rich-text-editor {
  border: 1px solid #d0d7e2;
  border-radius: 10px;
  overflow: hidden;
}
.rich-text-editor.is-disabled {
  opacity: 0.6;
  pointer-events: none;
}
</style>
```

- [ ] **Step 3: Verify build passes**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/shared/components/RichTextEditor.vue
git commit -m "Add RichTextEditor wrapper around Wangeditor 5"
```

---

### Task 16: `features/content` API layer and types

**Files:**
- Create: `frontend/src/features/content/types.ts`
- Create: `frontend/src/features/content/api/departments.ts`
- Create: `frontend/src/features/content/api/doctor-profiles.ts`
- Create: `frontend/src/features/content/api/media-upload.ts`
- Create: `frontend/src/features/content/api/index.ts`
- Create: `frontend/src/features/content/index.ts`

- [ ] **Step 1: Define types**

Create `frontend/src/features/content/types.ts`:

```typescript
export interface DepartmentCard {
  id: number
  slug: string
  name: string
  summary: string
  cover_image_url: string | null
  display_order: number
}

export interface DepartmentDetail extends DepartmentCard {
  description_html: string
}

export interface DepartmentAdminInput {
  name: string
  slug: string
  summary?: string
  description_html?: string
  display_order?: number
  is_published?: boolean
}

export interface DoctorDepartmentLink {
  slug: string
  name: string
  is_primary: boolean
}

export interface DoctorPortalCard {
  user_id: number
  name: string
  title: string
  specialty: string
  cover_image_url: string | null
  departments: DoctorDepartmentLink[]
}

export interface DoctorPortalDetail extends DoctorPortalCard {
  bio_published_html: string
}

export type DraftStatus = 'none' | 'pending' | 'approved' | 'rejected'

export interface DoctorProfileSelf {
  title: string
  specialty: string
  bio_published_html: string
  bio_draft_html: string
  cover_image_url: string | null
  is_published: boolean
  draft_status: DraftStatus
  draft_submitted_at: string | null
  draft_reviewed_at: string | null
  draft_review_note: string
  departments: DoctorDepartmentLink[]
}

export interface DoctorProfileAdmin extends DoctorProfileSelf {
  user_id: number
  username: string
  name: string
}

export interface AssignmentItem {
  department_id: number
  is_primary: boolean
}
```

- [ ] **Step 2: API modules**

Create `frontend/src/features/content/api/departments.ts`:

```typescript
import api from '@/shared/http/client'
import type { DepartmentAdminInput, DepartmentCard, DepartmentDetail } from '../types'

export interface PortalDepartmentDetailResponse {
  department: DepartmentDetail
  doctors: Array<{
    user_id: number
    name: string
    title: string
    specialty: string
    cover_image_url: string | null
    departments: Array<{ slug: string; name: string; is_primary: boolean }>
  }>
}

export const portalDepartmentsApi = {
  list(limit?: number): Promise<DepartmentCard[]> {
    return api
      .get<DepartmentCard[]>('/portal/departments/', { params: limit ? { limit } : {} })
      .then((r) => r.data)
  },
  detail(slug: string): Promise<PortalDepartmentDetailResponse> {
    return api.get<PortalDepartmentDetailResponse>(`/portal/departments/${slug}/`).then((r) => r.data)
  },
}

export const adminDepartmentsApi = {
  list(): Promise<DepartmentCard[]> {
    return api.get<DepartmentCard[]>('/admin/content/departments/').then((r) => r.data)
  },
  detail(id: number): Promise<DepartmentDetail> {
    return api.get<DepartmentDetail>(`/admin/content/departments/${id}/`).then((r) => r.data)
  },
  create(payload: DepartmentAdminInput): Promise<DepartmentDetail> {
    return api.post<DepartmentDetail>('/admin/content/departments/', payload).then((r) => r.data)
  },
  update(id: number, payload: Partial<DepartmentAdminInput>): Promise<DepartmentDetail> {
    return api.put<DepartmentDetail>(`/admin/content/departments/${id}/`, payload).then((r) => r.data)
  },
  remove(id: number): Promise<void> {
    return api.delete(`/admin/content/departments/${id}/`).then(() => undefined)
  },
}
```

Create `frontend/src/features/content/api/doctor-profiles.ts`:

```typescript
import api from '@/shared/http/client'
import type {
  AssignmentItem,
  DoctorPortalCard,
  DoctorPortalDetail,
  DoctorProfileAdmin,
  DoctorProfileSelf,
} from '../types'

export const portalDoctorsApi = {
  list(departmentSlug?: string): Promise<DoctorPortalCard[]> {
    return api
      .get<DoctorPortalCard[]>('/portal/doctors/', {
        params: departmentSlug ? { department: departmentSlug } : {},
      })
      .then((r) => r.data)
  },
  detail(userId: number): Promise<DoctorPortalDetail> {
    return api.get<DoctorPortalDetail>(`/portal/doctors/${userId}/`).then((r) => r.data)
  },
}

export const adminDoctorProfilesApi = {
  list(): Promise<DoctorProfileAdmin[]> {
    return api.get<DoctorProfileAdmin[]>('/admin/content/doctor-profiles/').then((r) => r.data)
  },
  detail(userId: number): Promise<DoctorProfileAdmin> {
    return api
      .get<DoctorProfileAdmin>(`/admin/content/doctor-profiles/${userId}/`)
      .then((r) => r.data)
  },
  update(userId: number, payload: Partial<DoctorProfileAdmin>): Promise<DoctorProfileAdmin> {
    return api
      .put<DoctorProfileAdmin>(`/admin/content/doctor-profiles/${userId}/`, payload)
      .then((r) => r.data)
  },
  setDepartments(userId: number, items: AssignmentItem[]): Promise<DoctorProfileAdmin> {
    return api
      .put<DoctorProfileAdmin>(
        `/admin/content/doctor-profiles/${userId}/departments/`,
        items,
      )
      .then((r) => r.data)
  },
  approve(userId: number): Promise<DoctorProfileAdmin> {
    return api
      .post<DoctorProfileAdmin>(`/admin/content/doctor-profiles/${userId}/approve/`)
      .then((r) => r.data)
  },
  reject(userId: number, note: string): Promise<DoctorProfileAdmin> {
    return api
      .post<DoctorProfileAdmin>(`/admin/content/doctor-profiles/${userId}/reject/`, { note })
      .then((r) => r.data)
  },
  pendingReviews(): Promise<DoctorProfileAdmin[]> {
    return api
      .get<DoctorProfileAdmin[]>('/admin/content/pending-reviews/')
      .then((r) => r.data)
  },
}

export const doctorSelfApi = {
  me(): Promise<DoctorProfileSelf> {
    return api.get<DoctorProfileSelf>('/doctor/content/profile/me/').then((r) => r.data)
  },
  save(payload: Partial<DoctorProfileSelf>): Promise<DoctorProfileSelf> {
    return api.put<DoctorProfileSelf>('/doctor/content/profile/me/', payload).then((r) => r.data)
  },
  submitReview(): Promise<DoctorProfileSelf> {
    return api
      .post<DoctorProfileSelf>('/doctor/content/profile/me/submit-review/')
      .then((r) => r.data)
  },
}
```

Create `frontend/src/features/content/api/media-upload.ts`:

```typescript
import api from '@/shared/http/client'

export async function uploadMedia(file: File): Promise<string> {
  const data = new FormData()
  data.append('file', file)
  const res = await api.post<{ url: string }>('/media/upload/', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data.url
}
```

Create `frontend/src/features/content/api/index.ts`:

```typescript
export * from './departments'
export * from './doctor-profiles'
export * from './media-upload'
```

Create `frontend/src/features/content/index.ts`:

```typescript
export * from './api'
export * from './types'
```

- [ ] **Step 3: Verify type-check passes**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/content/
git commit -m "Add content feature API layer and types"
```

---

### Task 17: Shared content components

**Files:**
- Create: `frontend/src/features/content/components/DepartmentCard.vue`
- Create: `frontend/src/features/content/components/DepartmentCarousel.vue`
- Create: `frontend/src/features/content/components/DoctorCard.vue`
- Create: `frontend/src/features/content/components/PublishStatusBadge.vue`
- Create: `frontend/src/features/content/composables/usePortalDepartments.ts`
- Create: `frontend/src/features/content/composables/useDraftReview.ts`
- Create: `frontend/src/features/content/__tests__/DepartmentCarousel.spec.ts`
- Create: `frontend/src/features/content/__tests__/PublishStatusBadge.spec.ts`

- [ ] **Step 1: `DepartmentCard.vue`**

Create `frontend/src/features/content/components/DepartmentCard.vue`:

```vue
<script setup lang="ts">
import type { DepartmentCard as Card } from '../types'

defineProps<{ department: Card }>()
</script>

<template>
  <article class="dept-card">
    <div class="dept-card__cover" :style="department.cover_image_url ? `background-image:url(${department.cover_image_url})` : ''">
      <span v-if="!department.cover_image_url" class="dept-card__placeholder">{{ department.name.charAt(0) }}</span>
    </div>
    <div class="dept-card__body">
      <h3 class="dept-card__title">{{ department.name }}</h3>
      <p class="dept-card__summary">{{ department.summary }}</p>
    </div>
  </article>
</template>

<style scoped>
.dept-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 6px 18px rgba(38, 53, 88, 0.08);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.dept-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(38, 53, 88, 0.14);
}
.dept-card__cover {
  height: 140px;
  background: linear-gradient(135deg, #4f73ea, #2e57db);
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dept-card__placeholder {
  font-size: 48px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 700;
}
.dept-card__body {
  padding: 16px 18px;
}
.dept-card__title {
  margin: 0 0 6px;
  font-size: 16px;
  color: #1f2f4e;
}
.dept-card__summary {
  margin: 0;
  font-size: 13px;
  color: #6f7894;
  line-height: 1.5;
}
</style>
```

- [ ] **Step 2: `DepartmentCarousel.vue`**

Create `frontend/src/features/content/components/DepartmentCarousel.vue`:

```vue
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { DepartmentCard } from '../types'
import { portalDepartmentsApi } from '../api/departments'

const props = withDefaults(defineProps<{ intervalMs?: number; limit?: number }>(), {
  intervalMs: 4000,
  limit: 5,
})

const router = useRouter()
const items = ref<DepartmentCard[]>([])
const current = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const visible = computed(() => items.value[current.value])

const advance = () => {
  if (items.value.length === 0) return
  current.value = (current.value + 1) % items.value.length
}

const start = () => {
  if (timer) return
  timer = setInterval(advance, props.intervalMs)
}

const stop = () => {
  if (timer) clearInterval(timer)
  timer = null
}

const go = (idx: number) => {
  current.value = idx
}

const goTo = (slug: string) => {
  router.push(`/portal/departments/${slug}`)
}

onMounted(async () => {
  try {
    items.value = await portalDepartmentsApi.list(props.limit)
    start()
  } catch {
    // swallow — login page should still render without portal data
  }
})

onBeforeUnmount(stop)
</script>

<template>
  <div v-if="items.length" class="dept-carousel" @mouseenter="stop" @mouseleave="start">
    <div class="dept-carousel__card" @click="visible && goTo(visible.slug)">
      <h4>{{ visible?.name }}</h4>
      <p>{{ visible?.summary }}</p>
    </div>
    <div class="dept-carousel__dots">
      <button
        v-for="(item, idx) in items"
        :key="item.id"
        :class="{ active: idx === current }"
        :aria-label="`Show ${item.name}`"
        @click="go(idx)"
      />
    </div>
  </div>
</template>

<style scoped>
.dept-carousel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.dept-carousel__card {
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 14px;
  padding: 18px 22px;
  color: #fff;
  cursor: pointer;
  transition: background 0.18s ease;
}
.dept-carousel__card:hover {
  background: rgba(255, 255, 255, 0.2);
}
.dept-carousel__card h4 {
  margin: 0 0 6px;
  font-size: 16px;
}
.dept-carousel__card p {
  margin: 0;
  font-size: 13px;
  opacity: 0.85;
}
.dept-carousel__dots {
  display: flex;
  gap: 6px;
}
.dept-carousel__dots button {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 0;
  padding: 0;
  background: rgba(255, 255, 255, 0.4);
  cursor: pointer;
}
.dept-carousel__dots button.active {
  background: #fff;
}
</style>
```

- [ ] **Step 3: `DoctorCard.vue`**

Create `frontend/src/features/content/components/DoctorCard.vue`:

```vue
<script setup lang="ts">
import type { DoctorPortalCard } from '../types'

defineProps<{ doctor: DoctorPortalCard }>()
</script>

<template>
  <article class="doctor-card">
    <div class="doctor-card__avatar">
      <img v-if="doctor.cover_image_url" :src="doctor.cover_image_url" :alt="doctor.name" />
      <span v-else>{{ doctor.name.charAt(0) }}</span>
    </div>
    <div class="doctor-card__body">
      <h4 class="doctor-card__name">{{ doctor.name }}</h4>
      <p class="doctor-card__title">{{ doctor.title }}</p>
      <p class="doctor-card__specialty">{{ doctor.specialty }}</p>
      <div class="doctor-card__tags">
        <span v-for="d in doctor.departments" :key="d.slug" :class="{ primary: d.is_primary }">
          {{ d.name }}
        </span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.doctor-card { display: flex; gap: 14px; padding: 14px; border-radius: 12px; background: #fff; box-shadow: 0 4px 14px rgba(38, 53, 88, 0.08); }
.doctor-card__avatar { width: 64px; height: 64px; border-radius: 50%; background: #e8eefa; overflow: hidden; display: flex; align-items: center; justify-content: center; font-size: 22px; color: #4f73ea; font-weight: 700; }
.doctor-card__avatar img { width: 100%; height: 100%; object-fit: cover; }
.doctor-card__name { margin: 0; font-size: 15px; color: #1f2f4e; }
.doctor-card__title { margin: 2px 0 0; font-size: 12px; color: #6f7894; }
.doctor-card__specialty { margin: 4px 0 0; font-size: 13px; color: #2e3a59; }
.doctor-card__tags { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px; }
.doctor-card__tags span { font-size: 11px; padding: 2px 8px; border-radius: 999px; background: #eef3fb; color: #4f73ea; }
.doctor-card__tags span.primary { background: #4f73ea; color: #fff; }
</style>
```

- [ ] **Step 4: `PublishStatusBadge.vue`**

Create `frontend/src/features/content/components/PublishStatusBadge.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { DraftStatus } from '../types'

const props = defineProps<{ status: DraftStatus; published?: boolean }>()

const label = computed(() => {
  switch (props.status) {
    case 'pending': return 'Pending review'
    case 'approved': return props.published ? 'Published' : 'Approved'
    case 'rejected': return 'Rejected'
    default: return props.published ? 'Published' : 'Draft'
  }
})

const variant = computed(() => {
  if (props.status === 'pending') return 'pending'
  if (props.status === 'rejected') return 'rejected'
  if (props.status === 'approved' || props.published) return 'published'
  return 'draft'
})
</script>

<template>
  <span class="status-badge" :data-variant="variant">{{ label }}</span>
</template>

<style scoped>
.status-badge { display: inline-flex; align-items: center; font-size: 12px; padding: 2px 10px; border-radius: 999px; font-weight: 600; }
.status-badge[data-variant='published'] { background: #e6f4ea; color: #1e7a36; }
.status-badge[data-variant='pending'] { background: #fff6e2; color: #b27800; }
.status-badge[data-variant='rejected'] { background: #fdecee; color: #b1273a; }
.status-badge[data-variant='draft'] { background: #eef0f6; color: #5b6478; }
</style>
```

- [ ] **Step 5: Composables**

Create `frontend/src/features/content/composables/usePortalDepartments.ts`:

```typescript
import { ref } from 'vue'
import { portalDepartmentsApi } from '../api/departments'
import type { DepartmentCard } from '../types'

export function usePortalDepartments() {
  const items = ref<DepartmentCard[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const load = async (limit?: number) => {
    loading.value = true
    error.value = null
    try {
      items.value = await portalDepartmentsApi.list(limit)
    } catch (e) {
      error.value = (e as Error).message ?? 'failed to load departments'
    } finally {
      loading.value = false
    }
  }

  return { items, loading, error, load }
}
```

Create `frontend/src/features/content/composables/useDraftReview.ts`:

```typescript
import { computed, type Ref } from 'vue'
import type { DoctorProfileSelf } from '../types'

export function useDraftReview(profile: Ref<DoctorProfileSelf | null>) {
  const isLocked = computed(() => profile.value?.draft_status === 'pending')
  const canSubmit = computed(() => profile.value?.draft_status === 'none')
  const wasRejected = computed(() => profile.value?.draft_status === 'rejected')
  const wasApproved = computed(() => profile.value?.draft_status === 'approved')
  return { isLocked, canSubmit, wasRejected, wasApproved }
}
```

- [ ] **Step 6: Tests**

Create `frontend/src/features/content/__tests__/PublishStatusBadge.spec.ts`:

```typescript
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PublishStatusBadge from '../components/PublishStatusBadge.vue'

describe('PublishStatusBadge', () => {
  it('renders pending', () => {
    const w = mount(PublishStatusBadge, { props: { status: 'pending' } })
    expect(w.text()).toContain('Pending review')
    expect(w.attributes('data-variant')).toBe('pending')
  })
  it('shows published when approved + published', () => {
    const w = mount(PublishStatusBadge, { props: { status: 'approved', published: true } })
    expect(w.text()).toContain('Published')
  })
  it('shows rejected', () => {
    const w = mount(PublishStatusBadge, { props: { status: 'rejected' } })
    expect(w.attributes('data-variant')).toBe('rejected')
  })
})
```

Create `frontend/src/features/content/__tests__/DepartmentCarousel.spec.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import DepartmentCarousel from '../components/DepartmentCarousel.vue'

vi.mock('../api/departments', () => ({
  portalDepartmentsApi: {
    list: vi.fn(async () => [
      { id: 1, slug: 'a', name: 'A', summary: 'sa', cover_image_url: null, display_order: 0 },
      { id: 2, slug: 'b', name: 'B', summary: 'sb', cover_image_url: null, display_order: 1 },
    ]),
  },
}))

const router = {
  push: vi.fn(),
}
vi.mock('vue-router', () => ({
  useRouter: () => router,
}))

afterEach(() => vi.clearAllMocks())

describe('DepartmentCarousel', () => {
  it('renders fetched items and routes on click', async () => {
    vi.useFakeTimers()
    const w = mount(DepartmentCarousel, { props: { intervalMs: 1000 } })
    await flushPromises()
    expect(w.text()).toContain('A')

    vi.advanceTimersByTime(1000)
    await flushPromises()
    expect(w.text()).toContain('B')

    await w.find('.dept-carousel__card').trigger('click')
    expect(router.push).toHaveBeenCalledWith('/portal/departments/b')
    vi.useRealTimers()
  })
})
```

- [ ] **Step 7: Run vitest**

```bash
cd frontend && npm run test -- --run
```

Expected: all tests pass (existing + new).

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/content/components/ frontend/src/features/content/composables/ frontend/src/features/content/__tests__/
git commit -m "Add content components (cards, carousel, badge) and composables"
```

---

## Phase 7 — Frontend pages & integration

### Task 18: Portal pages and router registration

**Files:**
- Create: `frontend/src/features/content/pages/portal/PortalDepartmentList.vue`
- Create: `frontend/src/features/content/pages/portal/PortalDepartmentDetail.vue`
- Create: `frontend/src/features/content/pages/portal/PortalDoctorList.vue`
- Create: `frontend/src/features/content/pages/portal/PortalDoctorDetail.vue`
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: `PortalDepartmentList.vue`**

Create `frontend/src/features/content/pages/portal/PortalDepartmentList.vue`:

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DepartmentCard from '../../components/DepartmentCard.vue'
import { usePortalDepartments } from '../../composables/usePortalDepartments'

const { items, loading, error, load } = usePortalDepartments()
const router = useRouter()

onMounted(() => load())
</script>

<template>
  <main class="portal-page">
    <header class="portal-page__header">
      <h1>Departments</h1>
      <p>Browse our clinical departments and find the right team.</p>
    </header>
    <div v-if="loading" class="portal-page__loading">Loading…</div>
    <div v-else-if="error" class="portal-page__error">{{ error }}</div>
    <div v-else class="portal-page__grid">
      <DepartmentCard
        v-for="d in items"
        :key="d.id"
        :department="d"
        @click="router.push(`/portal/departments/${d.slug}`)"
      />
    </div>
  </main>
</template>

<style scoped>
.portal-page { max-width: 1120px; margin: 0 auto; padding: 48px 24px; }
.portal-page__header h1 { margin: 0; font-size: 32px; color: #1f2f4e; }
.portal-page__header p { margin: 8px 0 28px; color: #6f7894; }
.portal-page__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 22px; }
.portal-page__loading, .portal-page__error { padding: 60px 0; text-align: center; color: #6f7894; }
</style>
```

- [ ] **Step 2: `PortalDepartmentDetail.vue`**

Create `frontend/src/features/content/pages/portal/PortalDepartmentDetail.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DoctorCard from '../../components/DoctorCard.vue'
import { portalDepartmentsApi, type PortalDepartmentDetailResponse } from '../../api/departments'

const route = useRoute()
const router = useRouter()
const data = ref<PortalDepartmentDetailResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const load = async () => {
  loading.value = true
  error.value = null
  try {
    data.value = await portalDepartmentsApi.detail(String(route.params.slug))
    if (data.value?.department.name) {
      document.title = `${data.value.department.name} – Departments`
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.slug, load)
</script>

<template>
  <main class="portal-page" v-if="!loading && data">
    <button class="back" @click="router.push('/portal/departments')">← All departments</button>
    <header class="portal-page__hero">
      <h1>{{ data.department.name }}</h1>
      <p>{{ data.department.summary }}</p>
    </header>
    <article class="portal-page__body" v-html="data.department.description_html" />
    <section class="portal-page__doctors">
      <h2>Doctors in this department</h2>
      <div class="portal-page__doctor-grid">
        <DoctorCard
          v-for="doc in data.doctors"
          :key="doc.user_id"
          :doctor="doc"
          @click="router.push(`/portal/doctors/${doc.user_id}`)"
        />
      </div>
    </section>
  </main>
  <div v-else-if="loading" class="portal-page__loading">Loading…</div>
  <div v-else-if="error" class="portal-page__error">{{ error }}</div>
</template>

<style scoped>
.portal-page { max-width: 880px; margin: 0 auto; padding: 32px 24px 64px; }
.back { background: none; border: 0; color: #4f73ea; padding: 0; cursor: pointer; font-size: 14px; }
.portal-page__hero h1 { margin: 12px 0 4px; font-size: 32px; color: #1f2f4e; }
.portal-page__hero p { margin: 0 0 32px; color: #6f7894; }
.portal-page__body :deep(img) { max-width: 100%; height: auto; border-radius: 10px; }
.portal-page__body :deep(h2), .portal-page__body :deep(h3) { margin-top: 24px; }
.portal-page__doctors h2 { margin: 40px 0 16px; font-size: 22px; }
.portal-page__doctor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.portal-page__loading, .portal-page__error { padding: 60px 0; text-align: center; color: #6f7894; }
</style>
```

- [ ] **Step 3: `PortalDoctorList.vue`**

Create `frontend/src/features/content/pages/portal/PortalDoctorList.vue`:

```vue
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DoctorCard from '../../components/DoctorCard.vue'
import { portalDoctorsApi } from '../../api/doctor-profiles'
import type { DoctorPortalCard } from '../../types'

const route = useRoute()
const router = useRouter()
const items = ref<DoctorPortalCard[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const departmentSlug = computed(() => {
  const q = route.query.department
  return typeof q === 'string' ? q : undefined
})

const load = async () => {
  loading.value = true
  error.value = null
  try {
    items.value = await portalDoctorsApi.list(departmentSlug.value)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="portal-page">
    <header class="portal-page__header">
      <h1>Doctors</h1>
      <p>Meet our medical team.</p>
    </header>
    <div v-if="loading" class="portal-page__loading">Loading…</div>
    <div v-else-if="error" class="portal-page__error">{{ error }}</div>
    <div v-else class="portal-page__grid">
      <DoctorCard
        v-for="doc in items"
        :key="doc.user_id"
        :doctor="doc"
        @click="router.push(`/portal/doctors/${doc.user_id}`)"
      />
    </div>
  </main>
</template>

<style scoped>
.portal-page { max-width: 1120px; margin: 0 auto; padding: 48px 24px; }
.portal-page__header h1 { margin: 0; font-size: 32px; color: #1f2f4e; }
.portal-page__header p { margin: 8px 0 28px; color: #6f7894; }
.portal-page__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.portal-page__loading, .portal-page__error { padding: 60px 0; text-align: center; color: #6f7894; }
</style>
```

- [ ] **Step 4: `PortalDoctorDetail.vue`**

Create `frontend/src/features/content/pages/portal/PortalDoctorDetail.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { portalDoctorsApi } from '../../api/doctor-profiles'
import type { DoctorPortalDetail } from '../../types'

const route = useRoute()
const router = useRouter()
const doctor = ref<DoctorPortalDetail | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const load = async () => {
  loading.value = true
  try {
    doctor.value = await portalDoctorsApi.detail(Number(route.params.userId))
    if (doctor.value?.name) {
      document.title = `${doctor.value.name} – Doctors`
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="portal-page" v-if="!loading && doctor">
    <button class="back" @click="router.push('/portal/doctors')">← All doctors</button>
    <header class="portal-page__hero">
      <div class="portal-page__avatar">
        <img v-if="doctor.cover_image_url" :src="doctor.cover_image_url" :alt="doctor.name" />
        <span v-else>{{ doctor.name.charAt(0) }}</span>
      </div>
      <div>
        <h1>{{ doctor.name }}</h1>
        <p>{{ doctor.title }} · {{ doctor.specialty }}</p>
        <div class="portal-page__tags">
          <span v-for="d in doctor.departments" :key="d.slug" :class="{ primary: d.is_primary }">{{ d.name }}</span>
        </div>
      </div>
    </header>
    <article class="portal-page__body" v-html="doctor.bio_published_html" />
  </main>
  <div v-else-if="loading" class="portal-page__loading">Loading…</div>
  <div v-else-if="error" class="portal-page__error">{{ error }}</div>
</template>

<style scoped>
.portal-page { max-width: 880px; margin: 0 auto; padding: 32px 24px 64px; }
.back { background: none; border: 0; color: #4f73ea; padding: 0; cursor: pointer; font-size: 14px; }
.portal-page__hero { display: flex; gap: 20px; align-items: center; margin: 16px 0 28px; }
.portal-page__avatar { width: 96px; height: 96px; border-radius: 50%; overflow: hidden; background: #e8eefa; display: flex; align-items: center; justify-content: center; font-size: 36px; color: #4f73ea; font-weight: 700; }
.portal-page__avatar img { width: 100%; height: 100%; object-fit: cover; }
.portal-page__hero h1 { margin: 0; }
.portal-page__hero p { margin: 4px 0; color: #6f7894; }
.portal-page__tags { margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; }
.portal-page__tags span { font-size: 12px; padding: 2px 10px; border-radius: 999px; background: #eef3fb; color: #4f73ea; }
.portal-page__tags span.primary { background: #4f73ea; color: #fff; }
.portal-page__body :deep(img) { max-width: 100%; height: auto; border-radius: 10px; }
.portal-page__loading, .portal-page__error { padding: 60px 0; text-align: center; color: #6f7894; }
</style>
```

- [ ] **Step 5: Register routes**

Edit `frontend/src/router/index.ts`. Inside the `routes: [...]` array, add the portal routes after the `/login` entry:

```typescript
    {
      path: '/portal/departments',
      name: 'portal-department-list',
      component: () => import('@/features/content/pages/portal/PortalDepartmentList.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/portal/departments/:slug',
      name: 'portal-department-detail',
      component: () => import('@/features/content/pages/portal/PortalDepartmentDetail.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/portal/doctors',
      name: 'portal-doctor-list',
      component: () => import('@/features/content/pages/portal/PortalDoctorList.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/portal/doctors/:userId',
      name: 'portal-doctor-detail',
      component: () => import('@/features/content/pages/portal/PortalDoctorDetail.vue'),
      meta: { requiresAuth: false },
    },
```

> Note: the existing guard is opt-in (`if (to.meta.requiresAuth && !auth.isAuthenticated)`). Portal routes set `requiresAuth: false`, so the guard won't redirect. No guard change needed. Also remove the existing redirect logic that forces authenticated users away from `/login` onto `/dashboard` if it conflicts with `/portal/*` — verify by reading the file: the current guard only intercepts `/login`, so portal routes are unaffected.

- [ ] **Step 6: Manual smoke test**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173/portal/departments` in an incognito window (to confirm unauthenticated access works). Expected: page renders. If the backend is empty, the grid will be empty — that's fine.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/content/pages/portal/ frontend/src/router/index.ts
git commit -m "Add public portal pages and routes for departments and doctors"
```

---

### Task 19: Admin pages

**Files:**
- Create: `frontend/src/features/content/pages/admin/AdminDepartmentList.vue`
- Create: `frontend/src/features/content/pages/admin/AdminDepartmentEdit.vue`
- Create: `frontend/src/features/content/pages/admin/AdminDoctorProfileList.vue`
- Create: `frontend/src/features/content/pages/admin/AdminDoctorProfileEdit.vue`
- Create: `frontend/src/features/content/pages/admin/AdminPendingReviews.vue`
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: `AdminDepartmentList.vue`**

Create `frontend/src/features/content/pages/admin/AdminDepartmentList.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElMessage, ElMessageBox, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { adminDepartmentsApi } from '../../api/departments'
import type { DepartmentCard } from '../../types'

const router = useRouter()
const items = ref<DepartmentCard[]>([])
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    items.value = await adminDepartmentsApi.list()
  } finally {
    loading.value = false
  }
}

const removeDept = async (id: number) => {
  await ElMessageBox.confirm('Delete this department?', 'Confirm', { type: 'warning' })
  await adminDepartmentsApi.remove(id)
  ElMessage.success('Deleted')
  await load()
}

onMounted(load)
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <h1>Departments</h1>
      <ElButton type="primary" @click="router.push('/admin/departments/new')">New department</ElButton>
    </header>
    <ElTable v-loading="loading" :data="items">
      <ElTableColumn prop="name" label="Name" />
      <ElTableColumn prop="slug" label="Slug" />
      <ElTableColumn prop="summary" label="Summary" />
      <ElTableColumn prop="display_order" label="Order" width="100" />
      <ElTableColumn label="Status" width="120">
        <template #default="{ row }">
          <ElTag :type="row.is_published ? 'success' : 'info'">
            {{ row.is_published ? 'Published' : 'Draft' }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn label="Actions" width="200">
        <template #default="{ row }">
          <ElButton size="small" @click="router.push(`/admin/departments/${row.id}`)">Edit</ElButton>
          <ElButton size="small" type="danger" @click="removeDept(row.id)">Delete</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; }
.admin-page__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.admin-page__header h1 { margin: 0; font-size: 22px; }
</style>
```

- [ ] **Step 2: `AdminDepartmentEdit.vue`**

Create `frontend/src/features/content/pages/admin/AdminDepartmentEdit.vue`:

```vue
<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElButton, ElForm, ElFormItem, ElInput, ElInputNumber, ElMessage, ElSwitch, ElUpload } from 'element-plus'
import type { UploadRawFile } from 'element-plus'
import RichTextEditor from '@/shared/components/RichTextEditor.vue'
import { adminDepartmentsApi } from '../../api/departments'
import { uploadMedia } from '../../api/media-upload'
import type { DepartmentAdminInput } from '../../types'

const route = useRoute()
const router = useRouter()
const isNew = computed(() => route.params.id === 'new')
const id = computed(() => (isNew.value ? null : Number(route.params.id)))

const form = reactive<DepartmentAdminInput & { cover_image_url: string | null }>({
  name: '', slug: '', summary: '', description_html: '',
  display_order: 0, is_published: false, cover_image_url: null,
})
const saving = ref(false)

const load = async () => {
  if (id.value == null) return
  const data = await adminDepartmentsApi.detail(id.value)
  Object.assign(form, data)
}

const handleCoverUpload = async (raw: UploadRawFile) => {
  const url = await uploadMedia(raw as File)
  form.cover_image_url = url
  ElMessage.success('Uploaded')
  return false
}

const save = async () => {
  saving.value = true
  try {
    if (isNew.value) {
      const created = await adminDepartmentsApi.create(form)
      ElMessage.success('Created')
      router.replace(`/admin/departments/${created.id}`)
    } else if (id.value != null) {
      await adminDepartmentsApi.update(id.value, form)
      ElMessage.success('Saved')
    }
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <h1>{{ isNew ? 'New department' : 'Edit department' }}</h1>
      <ElButton @click="router.push('/admin/departments')">Back</ElButton>
    </header>
    <ElForm :model="form" label-position="top" class="admin-form">
      <ElFormItem label="Name"><ElInput v-model="form.name" /></ElFormItem>
      <ElFormItem label="Slug"><ElInput v-model="form.slug" /></ElFormItem>
      <ElFormItem label="Summary"><ElInput v-model="form.summary" /></ElFormItem>
      <ElFormItem label="Description">
        <RichTextEditor v-model="form.description_html" />
      </ElFormItem>
      <ElFormItem label="Display order"><ElInputNumber v-model="form.display_order" :min="0" /></ElFormItem>
      <ElFormItem label="Published"><ElSwitch v-model="form.is_published" /></ElFormItem>
      <ElFormItem label="Cover image">
        <ElUpload :before-upload="handleCoverUpload" :show-file-list="false" accept="image/*">
          <ElButton>Upload cover</ElButton>
        </ElUpload>
        <img v-if="form.cover_image_url" :src="form.cover_image_url" class="admin-form__cover" />
      </ElFormItem>
      <div class="admin-form__actions">
        <ElButton type="primary" :loading="saving" @click="save">Save</ElButton>
      </div>
    </ElForm>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; max-width: 880px; }
.admin-page__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.admin-form { display: flex; flex-direction: column; gap: 4px; }
.admin-form__cover { display: block; margin-top: 12px; max-width: 240px; border-radius: 8px; }
.admin-form__actions { margin-top: 16px; }
</style>
```

- [ ] **Step 3: `AdminDoctorProfileList.vue`**

Create `frontend/src/features/content/pages/admin/AdminDoctorProfileList.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElTable, ElTableColumn } from 'element-plus'
import PublishStatusBadge from '../../components/PublishStatusBadge.vue'
import { adminDoctorProfilesApi } from '../../api/doctor-profiles'
import type { DoctorProfileAdmin } from '../../types'

const router = useRouter()
const items = ref<DoctorProfileAdmin[]>([])
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    items.value = await adminDoctorProfilesApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <h1>Doctor profiles</h1>
    </header>
    <ElTable v-loading="loading" :data="items">
      <ElTableColumn prop="name" label="Name" />
      <ElTableColumn prop="title" label="Title" />
      <ElTableColumn prop="specialty" label="Specialty" />
      <ElTableColumn label="Departments">
        <template #default="{ row }">
          <span v-for="d in row.departments" :key="d.slug" class="dept-tag" :class="{ primary: d.is_primary }">{{ d.name }}</span>
        </template>
      </ElTableColumn>
      <ElTableColumn label="Status" width="160">
        <template #default="{ row }">
          <PublishStatusBadge :status="row.draft_status" :published="row.is_published" />
        </template>
      </ElTableColumn>
      <ElTableColumn label="Actions" width="120">
        <template #default="{ row }">
          <ElButton size="small" @click="router.push(`/admin/doctor-profiles/${row.user_id}`)">Edit</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; }
.admin-page__header h1 { margin: 0 0 18px; font-size: 22px; }
.dept-tag { display: inline-flex; font-size: 12px; padding: 2px 8px; border-radius: 999px; background: #eef3fb; color: #4f73ea; margin-right: 4px; }
.dept-tag.primary { background: #4f73ea; color: #fff; }
</style>
```

- [ ] **Step 4: `AdminDoctorProfileEdit.vue`**

Create `frontend/src/features/content/pages/admin/AdminDoctorProfileEdit.vue`:

```vue
<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElButton, ElCheckbox, ElForm, ElFormItem, ElInput, ElInputNumber, ElMessage, ElRadio, ElRadioGroup, ElSwitch } from 'element-plus'
import RichTextEditor from '@/shared/components/RichTextEditor.vue'
import PublishStatusBadge from '../../components/PublishStatusBadge.vue'
import { adminDepartmentsApi } from '../../api/departments'
import { adminDoctorProfilesApi } from '../../api/doctor-profiles'
import type { AssignmentItem, DepartmentCard, DoctorProfileAdmin } from '../../types'

const route = useRoute()
const router = useRouter()
const userId = computed(() => Number(route.params.userId))

const profile = ref<DoctorProfileAdmin | null>(null)
const departments = ref<DepartmentCard[]>([])
const assignments = reactive<Record<number, { selected: boolean; is_primary: boolean }>>({})
const primaryId = ref<number | null>(null)
const saving = ref(false)

const loadAll = async () => {
  const [p, depts] = await Promise.all([
    adminDoctorProfilesApi.detail(userId.value),
    adminDepartmentsApi.list(),
  ])
  profile.value = p
  departments.value = depts
  for (const d of depts) assignments[d.id] = { selected: false, is_primary: false }
  for (const link of p.departments) {
    const match = depts.find((x) => x.slug === link.slug)
    if (match) {
      assignments[match.id].selected = true
      if (link.is_primary) {
        assignments[match.id].is_primary = true
        primaryId.value = match.id
      }
    }
  }
}

const save = async () => {
  if (!profile.value) return
  saving.value = true
  try {
    await adminDoctorProfilesApi.update(userId.value, {
      title: profile.value.title,
      specialty: profile.value.specialty,
      bio_draft_html: profile.value.bio_draft_html,
      bio_published_html: profile.value.bio_published_html,
      display_order: profile.value.display_order,
      is_published: profile.value.is_published,
    })
    const items: AssignmentItem[] = Object.entries(assignments)
      .filter(([, v]) => v.selected)
      .map(([id]) => ({
        department_id: Number(id),
        is_primary: Number(id) === primaryId.value,
      }))
    await adminDoctorProfilesApi.setDepartments(userId.value, items)
    ElMessage.success('Saved')
    await loadAll()
  } finally {
    saving.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <section class="admin-page" v-if="profile">
    <header class="admin-page__header">
      <h1>{{ profile.name }} ({{ profile.username }})</h1>
      <PublishStatusBadge :status="profile.draft_status" :published="profile.is_published" />
      <ElButton @click="router.push('/admin/doctor-profiles')">Back</ElButton>
    </header>
    <ElForm label-position="top" class="admin-form">
      <ElFormItem label="Title"><ElInput v-model="profile.title" /></ElFormItem>
      <ElFormItem label="Specialty"><ElInput v-model="profile.specialty" /></ElFormItem>
      <ElFormItem label="Published bio (live)"><RichTextEditor v-model="profile.bio_published_html" /></ElFormItem>
      <ElFormItem label="Draft bio"><RichTextEditor v-model="profile.bio_draft_html" /></ElFormItem>
      <ElFormItem label="Display order"><ElInputNumber v-model="profile.display_order" :min="0" /></ElFormItem>
      <ElFormItem label="Published"><ElSwitch v-model="profile.is_published" /></ElFormItem>
      <ElFormItem label="Departments">
        <div class="dept-grid">
          <div v-for="d in departments" :key="d.id" class="dept-row">
            <ElCheckbox v-model="assignments[d.id].selected">{{ d.name }}</ElCheckbox>
          </div>
        </div>
      </ElFormItem>
      <ElFormItem label="Primary department">
        <ElRadioGroup v-model="primaryId">
          <ElRadio v-for="d in departments.filter((x) => assignments[x.id].selected)" :key="d.id" :label="d.id">{{ d.name }}</ElRadio>
        </ElRadioGroup>
      </ElFormItem>
      <div class="admin-form__actions">
        <ElButton type="primary" :loading="saving" @click="save">Save</ElButton>
      </div>
    </ElForm>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; max-width: 960px; }
.admin-page__header { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.admin-page__header h1 { margin: 0; font-size: 22px; }
.admin-form__actions { margin-top: 16px; }
.dept-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 6px; }
</style>
```

- [ ] **Step 5: `AdminPendingReviews.vue`**

Create `frontend/src/features/content/pages/admin/AdminPendingReviews.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElButton, ElInput, ElMessage, ElMessageBox, ElTable, ElTableColumn } from 'element-plus'
import { adminDoctorProfilesApi } from '../../api/doctor-profiles'
import type { DoctorProfileAdmin } from '../../types'

const items = ref<DoctorProfileAdmin[]>([])
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    items.value = await adminDoctorProfilesApi.pendingReviews()
  } finally {
    loading.value = false
  }
}

const approve = async (userId: number) => {
  await adminDoctorProfilesApi.approve(userId)
  ElMessage.success('Approved')
  await load()
}

const reject = async (userId: number) => {
  const { value } = await ElMessageBox.prompt('Reason for rejection', 'Reject', {
    inputValidator: (v) => Boolean(v && v.trim().length),
    inputErrorMessage: 'reason is required',
  })
  await adminDoctorProfilesApi.reject(userId, value)
  ElMessage.success('Rejected')
  await load()
}

onMounted(load)
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header"><h1>Pending reviews</h1></header>
    <ElTable v-loading="loading" :data="items">
      <ElTableColumn prop="name" label="Doctor" />
      <ElTableColumn label="Draft preview">
        <template #default="{ row }">
          <div class="draft-preview" v-html="row.bio_draft_html" />
        </template>
      </ElTableColumn>
      <ElTableColumn prop="draft_submitted_at" label="Submitted" width="200" />
      <ElTableColumn label="Actions" width="220">
        <template #default="{ row }">
          <ElButton size="small" type="success" @click="approve(row.user_id)">Approve</ElButton>
          <ElButton size="small" type="danger" @click="reject(row.user_id)">Reject</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; }
.admin-page__header h1 { margin: 0 0 18px; font-size: 22px; }
.draft-preview { max-height: 120px; overflow: auto; font-size: 13px; color: #2e3a59; border: 1px dashed #d0d7e2; padding: 8px; border-radius: 6px; }
.draft-preview :deep(img) { max-width: 80px; }
</style>
```

- [ ] **Step 6: Register admin routes**

Edit `frontend/src/router/index.ts`. Add inside the routes array:

```typescript
    {
      path: '/admin/departments',
      name: 'admin-department-list',
      component: () => import('@/features/content/pages/admin/AdminDepartmentList.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/departments/:id',
      name: 'admin-department-edit',
      component: () => import('@/features/content/pages/admin/AdminDepartmentEdit.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/doctor-profiles',
      name: 'admin-doctor-profile-list',
      component: () => import('@/features/content/pages/admin/AdminDoctorProfileList.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/doctor-profiles/:userId',
      name: 'admin-doctor-profile-edit',
      component: () => import('@/features/content/pages/admin/AdminDoctorProfileEdit.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/reviews',
      name: 'admin-pending-reviews',
      component: () => import('@/features/content/pages/admin/AdminPendingReviews.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/content/pages/admin/ frontend/src/router/index.ts
git commit -m "Add admin content pages for departments, profiles, and reviews"
```

---

### Task 20: Doctor "My profile" page and route

**Files:**
- Create: `frontend/src/features/content/pages/doctor/DoctorMyProfile.vue`
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: `DoctorMyProfile.vue`**

Create `frontend/src/features/content/pages/doctor/DoctorMyProfile.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElAlert, ElButton, ElForm, ElFormItem, ElInput, ElMessage } from 'element-plus'
import RichTextEditor from '@/shared/components/RichTextEditor.vue'
import PublishStatusBadge from '../../components/PublishStatusBadge.vue'
import { doctorSelfApi } from '../../api/doctor-profiles'
import { useDraftReview } from '../../composables/useDraftReview'
import type { DoctorProfileSelf } from '../../types'

const profile = ref<DoctorProfileSelf | null>(null)
const saving = ref(false)
const submitting = ref(false)

const { isLocked, canSubmit, wasRejected, wasApproved } = useDraftReview(profile)

const load = async () => {
  profile.value = await doctorSelfApi.me()
}

const save = async () => {
  if (!profile.value) return
  saving.value = true
  try {
    profile.value = await doctorSelfApi.save({
      title: profile.value.title,
      specialty: profile.value.specialty,
      bio_draft_html: profile.value.bio_draft_html,
    })
    ElMessage.success('Saved')
  } catch (e: unknown) {
    const msg = (e as { response?: { status?: number } }).response?.status === 409
      ? 'Editing is locked while review is pending.'
      : 'Save failed'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

const submitForReview = async () => {
  submitting.value = true
  try {
    profile.value = await doctorSelfApi.submitReview()
    ElMessage.success('Submitted for review')
  } catch {
    ElMessage.error('Submit failed')
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="admin-page" v-if="profile">
    <header class="admin-page__header">
      <h1>My public profile</h1>
      <PublishStatusBadge :status="profile.draft_status" :published="profile.is_published" />
    </header>

    <ElAlert v-if="isLocked" type="warning" :closable="false" class="status-note">
      Your draft is awaiting review. Editing is locked until an admin approves or rejects it.
    </ElAlert>
    <ElAlert v-else-if="wasRejected" type="error" :closable="false" class="status-note">
      Last submission was rejected: {{ profile.draft_review_note || '(no note)' }}.
    </ElAlert>
    <ElAlert v-else-if="wasApproved" type="success" :closable="false" class="status-note">
      Latest version is published. Editing now will reset status to draft.
    </ElAlert>

    <ElForm label-position="top" class="admin-form">
      <ElFormItem label="Title"><ElInput v-model="profile.title" :disabled="isLocked" /></ElFormItem>
      <ElFormItem label="Specialty"><ElInput v-model="profile.specialty" :disabled="isLocked" /></ElFormItem>
      <ElFormItem label="Bio (draft — visible after admin approves)">
        <RichTextEditor v-model="profile.bio_draft_html" :disabled="isLocked" />
      </ElFormItem>
      <ElFormItem label="Currently published bio">
        <div class="published-preview" v-html="profile.bio_published_html || '<em>(nothing published yet)</em>'" />
      </ElFormItem>
      <div class="admin-form__actions">
        <ElButton :disabled="isLocked" :loading="saving" type="primary" @click="save">Save draft</ElButton>
        <ElButton :disabled="!canSubmit" :loading="submitting" type="success" @click="submitForReview">Submit for review</ElButton>
      </div>
    </ElForm>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; max-width: 880px; }
.admin-page__header { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }
.admin-page__header h1 { margin: 0; font-size: 22px; }
.status-note { margin-bottom: 16px; }
.published-preview { padding: 12px; background: #f7f9fc; border-radius: 8px; min-height: 80px; }
.published-preview :deep(img) { max-width: 200px; }
.admin-form__actions { margin-top: 16px; display: flex; gap: 12px; }
</style>
```

- [ ] **Step 2: Register route**

Edit `frontend/src/router/index.ts`. Add:

```typescript
    {
      path: '/doctor/profile',
      name: 'doctor-my-profile',
      component: () => import('@/features/content/pages/doctor/DoctorMyProfile.vue'),
      meta: { requiresAuth: true, roles: ['doctor'] },
    },
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/content/pages/doctor/ frontend/src/router/index.ts
git commit -m "Add doctor self-service profile page with submit-for-review"
```

---

### Task 21: Login-page carousel + sidebar nav additions

**Files:**
- Modify: `frontend/src/views/LoginPage.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Login page left-panel carousel**

Edit `frontend/src/views/LoginPage.vue`. At the top of `<script setup>`, add the import:

```typescript
import { useRouter as _useRouterUnused } from 'vue-router'  // (router already imported)
import DepartmentCarousel from '@/features/content/components/DepartmentCarousel.vue'
```

(Remove the duplicate import if `useRouter` is already imported; the relevant addition is the `DepartmentCarousel` import.)

Replace the existing `<section class="login-brand">` block with:

```vue
    <section class="login-brand">
      <div class="login-logo-wrap">
        <BrandLogo size="lg" />
      </div>
      <div class="login-hero">
        <h1>Streamline Your Medical Practice</h1>
        <p>Manage doctors, patients, and appointments all in one place.</p>
      </div>

      <div class="login-portal-preview">
        <DepartmentCarousel />
        <div class="login-portal-cta">
          <ElButton class="cta-btn" @click="router.push('/portal/departments')">Browse departments</ElButton>
          <ElButton class="cta-btn" @click="router.push('/portal/doctors')">Find a doctor</ElButton>
        </div>
      </div>
    </section>
```

Then append the supporting styles to the `<style scoped>` block (before the `@media` rule):

```css
.login-portal-preview {
  margin-top: 40px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.login-portal-cta {
  display: flex;
  gap: 12px;
}
.cta-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
  border-radius: 12px;
  padding: 10px 18px;
}
.cta-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}
```

Inside the `@media (max-width: 880px)` block, append:

```css
  .login-portal-preview { margin-top: 20px; }
```

- [ ] **Step 2: Add sidebar nav items**

Edit `frontend/src/App.vue`. In the icon import:

```typescript
import { DataLine, FirstAidKit, User, Calendar, Timer, Notebook, SwitchButton, OfficeBuilding, Memo, Edit } from '@element-plus/icons-vue'
```

In the `navItems` array, append:

```typescript
  { path: '/admin/departments', label: 'Departments', icon: OfficeBuilding, roles: ['admin'] },
  { path: '/admin/doctor-profiles', label: 'Doctor profiles', icon: FirstAidKit, roles: ['admin'] },
  { path: '/admin/reviews', label: 'Pending reviews', icon: Memo, roles: ['admin'] },
  { path: '/doctor/profile', label: 'My public profile', icon: Edit, roles: ['doctor'] },
```

Update `pageTitleMap` to include the new routes:

```typescript
const pageTitleMap: Record<string, string> = {
  login: 'Sign In',
  dashboard: 'Dashboard',
  doctors: 'Doctors',
  patients: 'Patients',
  appointments: 'Appointments',
  timeslots: 'Schedule',
  records: 'Medical Records',
  profile: 'Personal Center',
  'admin-department-list': 'Departments',
  'admin-department-edit': 'Department',
  'admin-doctor-profile-list': 'Doctor Profiles',
  'admin-doctor-profile-edit': 'Doctor Profile',
  'admin-pending-reviews': 'Pending Reviews',
  'doctor-my-profile': 'My Public Profile',
  'portal-department-list': 'Departments',
  'portal-department-detail': 'Department',
  'portal-doctor-list': 'Doctors',
  'portal-doctor-detail': 'Doctor',
}
```

- [ ] **Step 3: Manual smoke test**

```bash
cd frontend && npm run dev
```

Visit `http://localhost:5173/login` in incognito — left panel shows the carousel (or a blank space if no published departments yet). Buttons route into portal pages.

Then log in as admin — sidebar shows new Departments / Doctor profiles / Pending reviews entries.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/LoginPage.vue frontend/src/App.vue
git commit -m "Embed department carousel on login page and add content nav items"
```

---

### Task 22: Sitemap endpoint

**Files:**
- Create: `backend/sitemap_views.py`
- Modify: `backend/config/urls.py`
- Create: `backend/tests/content/test_sitemap.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/content/test_sitemap.py`:

```python
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
```

- [ ] **Step 2: Run test and confirm 404**

```bash
cd backend && pytest tests/content/test_sitemap.py -v
```

- [ ] **Step 3: Implement the view**

Create `backend/sitemap_views.py`:

```python
from __future__ import annotations

from django.http import HttpResponse
from django.views.decorators.http import require_GET

from content.models import Department, DoctorProfile


def _iso(dt) -> str:
    return dt.strftime("%Y-%m-%d") if dt else ""


@require_GET
def sitemap(request) -> HttpResponse:
    base = f"{request.scheme}://{request.get_host()}"
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    static_paths = [
        ("/portal/departments", ""),
        ("/portal/doctors", ""),
    ]
    for path, lastmod in static_paths:
        lines.append(f"<url><loc>{base}{path}</loc>")
        if lastmod:
            lines.append(f"<lastmod>{lastmod}</lastmod>")
        lines.append("</url>")
    for d in Department.objects.filter(is_published=True):
        lines.append(
            f"<url><loc>{base}/portal/departments/{d.slug}</loc>"
            f"<lastmod>{_iso(d.updated_at)}</lastmod></url>"
        )
    for p in DoctorProfile.objects.filter(is_published=True).select_related("user"):
        lines.append(
            f"<url><loc>{base}/portal/doctors/{p.user_id}</loc>"
            f"<lastmod>{_iso(p.updated_at)}</lastmod></url>"
        )
    lines.append("</urlset>")
    return HttpResponse("\n".join(lines), content_type="application/xml")
```

- [ ] **Step 4: Wire URL**

Edit `backend/config/urls.py`. Add to imports:

```python
from sitemap_views import sitemap
```

Add to `urlpatterns`:

```python
    path("sitemap.xml", sitemap),
```

- [ ] **Step 5: Run test**

```bash
cd backend && pytest tests/content/test_sitemap.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/sitemap_views.py backend/config/urls.py backend/tests/content/test_sitemap.py
git commit -m "Add /sitemap.xml listing published departments and doctors"
```

---

## Wrap-up

### Task 23: Docs, full test sweep, and manual acceptance

**Files:**
- Modify: `docs/internal/PRODUCT_OVERVIEW.md`
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `frontend/README.md`

- [ ] **Step 1: Update `PRODUCT_OVERVIEW.md`**

Edit `docs/internal/PRODUCT_OVERVIEW.md`. Under section 3, insert a new `3.7 Content Portal` subsection:

```markdown
## 3.7 Content Portal

- Public department directory at `/portal/departments` and detail pages at `/portal/departments/<slug>`
- Public doctor list at `/portal/doctors` and detail at `/portal/doctors/<id>`
- Login page left panel shows a carousel of published departments with quick links to `Browse departments` and `Find a doctor`
- Admin manages department content directly (CRUD)
- Doctor introductions follow a draft → submit → admin approve/reject → publish workflow with status states `none` / `pending` / `approved` / `rejected`
- Rich text supports inline images served from MinIO (S3-compatible)
- `sitemap.xml` exposes published portal URLs for search engines
```

Remove the matching bullet ("Add notification center" / etc.) from section 10 if it covers any of the items above, OR specifically remove a placeholder line about content. Reread §10 first and prune only what is now delivered.

- [ ] **Step 2: Update top-level `README.md`**

Edit `README.md`:

- In the architecture or tech-stack list, mention MinIO as an S3-compatible media store
- In the env / quick start section, point readers at the new MinIO variables in `.env.example`

(Keep additions surgical — don't rewrite the whole README.)

- [ ] **Step 3: Update `backend/README.md`**

Add `content` to the module map. Show that it owns Department/DoctorProfile/DoctorDepartment models, services for sanitization and the draft state machine, and the `/api/portal`, `/api/admin/content`, `/api/doctor/content`, `/api/media/upload` endpoints.

- [ ] **Step 4: Update `frontend/README.md`**

Add `features/content` to the feature list. Note `shared/components/RichTextEditor.vue` and the public portal routes `/portal/*`.

- [ ] **Step 5: Run full backend test suite + lint**

```bash
cd backend && ruff check . && black --check . && pytest -q
```

Expected: all green.

- [ ] **Step 6: Run full frontend test suite + build**

```bash
cd frontend && npm run test -- --run && npm run build
```

Expected: all tests pass, build succeeds.

- [ ] **Step 7: Walk the manual acceptance checklist**

From the spec's §8.3, walk through each item. For each failed step, fix the underlying bug, commit it as a follow-up, and rerun.

```
☐ docker compose up — minio:9000 reachable; bucket auto-created
☐ Admin creates 2–3 departments with cover images and embedded rich-text images
☐ Admin assigns 1–2 doctors per department; sets one as primary
☐ Doctor logs in, edits their introduction, submits for review → status becomes pending
☐ Admin sees the pending entry, approves it → bio_published_html is updated
☐ Admin rejects another submission with a note → Doctor sees the rejection note
☐ Anonymous browser visits /portal/departments → list renders
☐ /portal/departments/<slug> renders department detail with assigned doctors
☐ /portal/doctors/<id> renders rich-text bio with images served from MinIO
☐ /sitemap.xml lists every published portal URL
☐ Login page left panel carousel rotates and links navigate correctly
☐ Toggling is_published on a department immediately changes portal visibility
☐ Submitting a rich-text payload with <script>alert(1)</script> persists with the script stripped
☐ 70 consecutive portal requests from one IP — 61st onwards returns 429
```

- [ ] **Step 8: Commit the docs updates**

```bash
git add docs/internal/PRODUCT_OVERVIEW.md README.md backend/README.md frontend/README.md
git commit -m "Document content portal module across project docs"
```

- [ ] **Step 9: Optional — open a PR**

If working on a feature branch separate from `main`, open a PR for review. (Skip if working directly on `feature/performance-optimizations`.)

---

## Self-review checklist

This plan addresses each section of the design spec:

- **§2 Confirmed decisions** → Tasks 1–22 implement all of them; demo-environment "no migration" implicitly satisfied by not adding migrations beyond the `content` app's `0001_initial.py`.
- **§4 Data model** → Tasks 3–5.
- **§5 API surface** → Tasks 8 (serializers/perm/throttle), 9 (portal), 10 (admin), 11 (doctor), 12 (media), 22 (sitemap).
- **§6 Media storage** → Task 13 (compose + bootstrap + settings), Task 14 (smoke verification).
- **§7 Frontend structure** → Tasks 15–21.
- **§8 Test plan** → Tasks 3–12 cover backend unit/api tests; Task 17 covers the key Vitest cases; Task 23 walks the manual checklist.
- **§9 Documentation updates** → Task 23.
- **§10 Out of scope** → Not implemented (correctly).
- **§11 Risks** → MinIO env split, draft locking, partial unique on SQLite, bleach allowlist — all reflected in the implementation (Tasks 7, 11, 13, 6) and noted in the plan.

If you find a gap during execution, add a new task in-line rather than skipping it.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-12-departments-and-doctor-profiles.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Best for a 23-task plan like this since context stays clean.

2. **Inline Execution** — Execute tasks in this session with checkpoints. Good for tight oversight but the session window will fill quickly.

Which approach?






