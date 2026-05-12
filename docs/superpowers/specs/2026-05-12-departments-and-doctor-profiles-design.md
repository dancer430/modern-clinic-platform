# Departments & Doctor Profiles — Design Spec

**Status:** Draft for review
**Date:** 2026-05-12
**Author:** Brainstormed with Claude
**Scope:** Single OpenSpec change. Demo environment, no data migration required.

---

## 1. Goal

Add two content-driven modules — **Department introductions** and **Doctor introductions** — to the platform. Both support cover images and rich-text descriptions. Content is browseable by unauthenticated visitors as a public clinic portal, and feeds a preview carousel on the login page.

The platform shifts from a pure internal tool toward an internal tool + public clinic portal, while keeping the existing role-based backend and login flow untouched at the root path.

## 2. Confirmed Decisions

| Dimension | Decision |
|---|---|
| Audience | Public, unauthenticated visitors (patients before booking) |
| Doctor ↔ Department | Many-to-many via `DoctorDepartment` join table with `is_primary` |
| Editing model | Admin owns department content. Doctors edit their own introduction as a **draft**, Admin reviews and approves before publication |
| Media storage | New **MinIO** container, accessed via `django-storages` S3 backend |
| Rich-text editor | **Wangeditor 5** (`@wangeditor/editor-for-vue@next`) |
| Public path | Portal lives under `/portal/*`. Root `/` stays as login |
| Login-page enhancement | Left brand panel gains a published-department carousel + "Browse departments" / "Find a doctor" buttons |
| SEO | SPA + dynamic `<title>` / `<meta>` + `sitemap.xml`. No SSR |
| Scope | Single change, no phased delivery (demo environment) |
| Data migration | None — demo only |
| Rate limiting | DRF throttle on public endpoints: 60 req/min/IP |
| HTML sanitization | Server-side `bleach` allowlist on every persisted rich-text field |
| Doctor self-assignment to departments | **Not supported.** Admin assigns. Avoid bypassing the review workflow |

## 3. Module Inventory

1. **Backend data layer** — `Department`, `DoctorProfile`, `DoctorDepartment` models in a new `content` Django app
2. **Backend API layer** — `/api/admin/*`, `/api/doctor/*`, `/api/portal/*`, `/api/media/upload/`
3. **Media storage layer** — MinIO container + `django-storages` + bucket bootstrap
4. **Frontend backstage** — Admin department CRUD, pending-reviews queue, Doctor "My profile" editor
5. **Frontend portal** — `/portal/*` public pages, `sitemap.xml`, login-page carousel

Implementation order: 1 → 2 → 3 → 4 → 5.

## 4. Data Model

All new models live in a **new `content` Django app**, keeping `users` and `appointments` untouched.

### 4.1 `Department`

| Field | Type | Notes |
|---|---|---|
| `id` | PK | |
| `name` | `CharField(120, unique=True)` | |
| `slug` | `SlugField(140, unique=True)` | URL-friendly identifier, used in `/portal/departments/<slug>` |
| `summary` | `CharField(200)` | Short blurb for cards |
| `description_html` | `TextField` | Wangeditor output, sanitized on save |
| `cover_image` | `ImageField(storage=S3)` | Stored in MinIO `media/` prefix |
| `display_order` | `PositiveIntegerField(default=0)` | Lower = earlier |
| `is_published` | `BooleanField(default=False)` | Toggled by Admin only; no review workflow |
| `created_at` / `updated_at` | `DateTimeField` | |

### 4.2 `DoctorProfile`

Separate 1:1 table joined to `User` (not added to `User` directly), since these fields are doctor-specific.

| Field | Type | Notes |
|---|---|---|
| `user` | `OneToOneField(User, related_name='doctor_profile')` | |
| `title` | `CharField(80)` | e.g. "Senior Consultant" |
| `specialty` | `CharField(200)` | Short text shown on cards |
| `bio_published_html` | `TextField` | Public-facing version |
| `bio_draft_html` | `TextField` | Doctor's work-in-progress / pending content |
| `cover_image` | `ImageField(storage=S3)` | Distinct from the existing small avatar field on `User` |
| `display_order` | `PositiveIntegerField(default=0)` | |
| `is_published` | `BooleanField(default=False)` | Admin gate for public visibility |
| `draft_status` | `CharField` choices: `none` / `pending` / `approved` / `rejected` | |
| `draft_submitted_at` | `DateTimeField(null=True)` | |
| `draft_reviewed_at` | `DateTimeField(null=True)` | |
| `draft_review_note` | `TextField(blank=True)` | Filled when `rejected` |
| `created_at` / `updated_at` | | |

**Draft state machine:**

```
none      ──(doctor submits review)──→ pending
pending   ──(admin approves)       ──→ approved
pending   ──(admin rejects)        ──→ rejected
approved  ──(doctor edits via PUT) ──→ none
rejected  ──(doctor edits via PUT) ──→ none
none      ──(doctor submits review)──→ pending  (loop)
```

Service contracts per transition:

| Action | Allowed from | Effect |
|---|---|---|
| `submit_review()` | `none` | `draft_status='pending'`, `draft_submitted_at=now()` |
| `approve()` | `pending` | Copy `bio_draft_html` → `bio_published_html`; `draft_status='approved'`; `draft_reviewed_at=now()` |
| `reject(note)` | `pending` | `draft_status='rejected'`; `draft_review_note=note`; `draft_reviewed_at=now()` |
| Doctor `PUT /me/` | `none`, `approved`, `rejected` | Writes `bio_draft_html` etc.; if was `approved` or `rejected`, status drops to `none` |
| Doctor `PUT /me/` | `pending` | **Rejected with 409 Conflict** — editor must wait for review |

UI consequence: when `draft_status='approved'` and `bio_draft_html == bio_published_html`, the editor renders a "Published" badge; on edit, the badge transitions to "Unsubmitted changes".

### 4.3 `DoctorDepartment`

Join table.

| Field | Type | Notes |
|---|---|---|
| `doctor` | `FK(DoctorProfile)` | |
| `department` | `FK(Department)` | |
| `is_primary` | `BooleanField(default=False)` | |

Constraints:
- `UniqueConstraint(fields=['doctor', 'department'])`
- Partial unique constraint: at most one `is_primary=True` row per doctor (Postgres partial index; SQLite — enforce in service layer)

### 4.4 Rich-text image lifecycle

Images embedded in rich text are written into the HTML as `<img src="<minio-public-endpoint>/clinic-media/media/inline/...">`. No separate image registry table.

**Orphan cleanup** (images uploaded but no longer referenced): out of scope for this change. Acknowledge as future work.

## 5. API Surface

All responses use the existing uniform error envelope (introduced in commit `e999992`).

### 5.1 Public — `/api/portal/*` (no authentication, 60 req/min/IP throttle)

```
GET /api/portal/departments/?limit=N
    → [{id, slug, name, summary, cover_image_url, display_order}]
    Only is_published=True. Ordered by display_order, then name.

GET /api/portal/departments/<slug>/
    → {
        department: {id, slug, name, summary, description_html, cover_image_url, …},
        doctors: [{user_id, name, title, specialty, cover_image_url, is_primary}]
      }
    Doctors filtered to is_published=True.

GET /api/portal/doctors/?department=<slug>
    → [{user_id, name, title, specialty, cover_image_url, departments: [{slug, name, is_primary}]}]

GET /api/portal/doctors/<user_id>/
    → {user_id, name, title, specialty, bio_published_html, cover_image_url, departments: […]}
```

Draft fields are **never** returned by portal endpoints.

### 5.2 Admin — `/api/admin/*`

```
Departments:
GET    /api/admin/departments/             — full list including unpublished
POST   /api/admin/departments/             — create
GET    /api/admin/departments/<id>/
PUT    /api/admin/departments/<id>/
DELETE /api/admin/departments/<id>/

Doctor profiles:
GET    /api/admin/doctor-profiles/
GET    /api/admin/doctor-profiles/<user_id>/   — returns both published and draft fields
PUT    /api/admin/doctor-profiles/<user_id>/   — Admin direct edit (bypasses review)

Doctor ↔ Department assignment:
PUT    /api/admin/doctor-profiles/<user_id>/departments/
       Body: [{department_id, is_primary}]
       Service replaces the doctor's full set; enforces at most one is_primary.

Review workflow:
GET    /api/admin/pending-reviews/                    — list where draft_status=pending
POST   /api/admin/doctor-profiles/<user_id>/approve/
POST   /api/admin/doctor-profiles/<user_id>/reject/   Body: {note}
```

### 5.3 Doctor — `/api/doctor/*` (self only)

```
GET  /api/doctor/profile/me/
     → {published_html, draft_html, draft_status, draft_review_note, departments, …}

PUT  /api/doctor/profile/me/
     Body: {title, specialty, bio_draft_html, cover_image_url}
     → Saves draft. If draft_status was 'approved' or 'rejected', it drops to 'none'.
       If draft_status == 'pending', returns 409 Conflict — editor is locked during review.

POST /api/doctor/profile/me/submit-review/
     → Allowed only when draft_status == 'none'. Transitions to 'pending', stamps draft_submitted_at.
       Returns 409 if status is already 'pending'.

GET  /api/doctor/profile/me/departments/
     → Read-only view of own department assignments.
```

Doctors cannot modify their department assignments — that authority sits with Admin.

### 5.4 Media — `/api/media/upload/`

```
POST /api/media/upload/
     Multipart: file
     Auth: Admin or Doctor
     Validation: content-type in {png, jpg, jpeg, webp}; size ≤ 5 MB
     Stores under bucket `clinic-media/`, key prefix `media/inline/<uuid>.<ext>`
     Response: {url}
```

Used by the Wangeditor `customUpload` hook and by cover-image upload widgets.

### 5.5 Sitemap — `GET /sitemap.xml`

Not under `/api/` prefix. Returns standard `<urlset>` XML containing:
- `/portal/departments`
- `/portal/departments/<slug>` for each published department
- `/portal/doctors`
- `/portal/doctors/<user_id>` for each published doctor

`<lastmod>` uses each record's `updated_at`.

### 5.6 Sanitization

All rich-text input goes through `content/services.py::sanitize_html()`:

- **Allowed tags:** `p`, `h1`, `h2`, `h3`, `strong`, `em`, `u`, `ul`, `ol`, `li`, `blockquote`, `a`, `img`, `br`
- **Allowed attributes:** `href` (http/https only), `src` (must start with the platform MinIO public endpoint or be a relative `/media/...` path), `alt`, `title`
- **Stripped:** `script`, `style`, `iframe`, all `on*` handlers, inline `style=""`, color/size attributes

## 6. Media Storage Layer

### 6.1 docker-compose

Add a `minio` service with `minio_data` named volume, ports `9000:9000` (S3 API) and `9001:9001` (console), healthcheck against `/minio/health/live`.

`docker-compose.2c4g.yml` constrains `minio` to ~256 MB memory.

### 6.2 Bucket bootstrap

A backend bootstrap step (extends the existing entrypoint script) uses `mc` to:

1. Wait until MinIO is healthy
2. Create bucket `clinic-media` if missing
3. Apply anonymous read policy to the `media/*` prefix

Run idempotently on every container start.

### 6.3 New environment variables

```
MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=
MINIO_BUCKET=clinic-media
MINIO_ENDPOINT=http://minio:9000           # used by Django container → MinIO
MINIO_PUBLIC_ENDPOINT=http://localhost:9000 # used in URLs returned to browsers
```

### 6.4 Django settings

`STORAGES['default']` switches to `storages.backends.s3.S3Storage` with `custom_domain` set from `MINIO_PUBLIC_ENDPOINT` and `location='media'`.

New backend dependencies: `django-storages[s3]`, `boto3`, `bleach`, `Pillow`.

## 7. Frontend Structure

### 7.1 New `content` feature

```
frontend/src/features/content/
├── api/
│   ├── departments.ts
│   ├── doctor-profiles.ts
│   └── media-upload.ts
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
├── stores/
│   └── content-store.ts
└── types.ts
```

A reusable `frontend/src/shared/components/RichTextEditor.vue` wraps Wangeditor 5 and is consumed by admin/doctor editor pages.

### 7.2 Router & guards

Existing global router guard requires login on all routes. Update it to skip authentication when `to.path` starts with `/portal` (or `/login`):

```ts
const PUBLIC_PREFIXES = ['/login', '/portal']
if (PUBLIC_PREFIXES.some(p => to.path.startsWith(p))) return next()
```

Every portal route's `meta` carries `title` and `description`. A `router.afterEach` hook syncs these into `document.title` and `<meta name="description">`.

### 7.3 Login-page carousel

`frontend/src/views/LoginPage.vue` left brand panel:

- Top: existing logo + a tightened headline
- Middle: `<DepartmentCarousel />` — auto-rotates every 4 s, clickable cards routing to `/portal/departments/<slug>`, dot indicator below. Data: `GET /api/portal/departments/?limit=5` on mount
- Bottom: two buttons — "Browse departments" → `/portal/departments`, "Find a doctor" → `/portal/doctors`

Visual style retains the existing blue gradient + blurred orbs; cards use a glassmorphism treatment (translucent white, backdrop blur) so they sit naturally on the gradient.

### 7.4 Backstage navigation

- Admin sidebar gains a "Content" group with three items: Departments, Doctor profiles, Pending reviews (badge showing pending count)
- Doctor sidebar gains "My public profile"

### 7.5 Wangeditor configuration

- Toolbar restricted to: headings (H1–H3), bold/italic/underline, unordered/ordered list, blockquote, link, image, clear-format
- `customUpload` posts to `/api/media/upload/`, inserts returned URL into the document
- No color, no font size, no table — keeps content style consistent across the portal

## 8. Test & Verification Plan

### 8.1 Backend (pytest)

**Model layer**
- `Department.slug` auto-generation from `name`, uniqueness enforced
- `DoctorProfile.draft_status` legal transitions; illegal transitions raise
- `DoctorDepartment`: cannot have two `is_primary=True` for the same doctor

**Service layer**
- `sanitize_html()` strips `<script>`, `<iframe>`, `on*` attributes; keeps allowed tags
- `sanitize_html()` rewrites or drops `<img>` whose `src` is not in the allowlist
- `approve_doctor_profile()` copies `bio_draft_html` → `bio_published_html`, sets `draft_reviewed_at`
- `reject_doctor_profile(note)` sets status to `rejected`, persists `note`

**API layer**
- Portal endpoints reachable without `Authorization`; admin and doctor endpoints reject anonymous access
- Portal endpoints exclude `is_published=False` rows
- Doctor `/me/` endpoints reject access to other doctors' data
- Portal throttle returns 429 on the 61st request from a single IP within 1 min
- `/api/media/upload/` rejects non-images and files >5 MB

Target: ~25–30 new test cases. Suite remains ruff/black/pytest green at the existing baseline.

### 8.2 Frontend (vitest)

- `DepartmentCard.vue` renders props as expected (snapshot)
- `DepartmentCarousel.vue` advances on its timer; clicking a card navigates to the expected route
- `RichTextEditor.vue` two-way binds `modelValue`; `customUpload` invokes the upload API
- `PublishStatusBadge.vue` renders the correct visual per `draft_status`
- `usePortalDepartments` composable returns happy-path data; surfaces errors

### 8.3 Manual acceptance checklist

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

## 9. Documentation Updates

- `docs/internal/PRODUCT_OVERVIEW.md` — add section "3.7 Content Portal"; remove the matching item from the "Next steps" list
- `README.md` — architecture mention of MinIO; new `.env` entries
- `backend/README.md` — module map includes `content`
- `frontend/README.md` — feature list includes `content`

## 10. Out of Scope

The following are deliberately deferred and called out so they do not creep into this change:

- Orphan-image cleanup job
- "Doctor requests to join department" workflow (`DepartmentJoinRequest`)
- Specialty tags / searchable medical-condition taxonomy
- Full-text search across portal content
- SSR / vite-ssg for SEO beyond meta tags
- Multi-clinic / multi-tenant content
- Internationalization of portal content (single-language for now)
- Sharing / social-card metadata (Open Graph) beyond the basic `<meta name="description">`

## 11. Risks & Open Items

| Risk | Mitigation |
|---|---|
| MinIO public endpoint URL mismatch between container-internal and browser-facing access | Two env vars (`MINIO_ENDPOINT`, `MINIO_PUBLIC_ENDPOINT`); document clearly in `.env.example` |
| Rich-text payload size grows unbounded | `bio_draft_html` / `bio_published_html` enforce a 200 KB ceiling at the serializer |
| Doctor edits while a submission is pending | UI disables the editor while `draft_status='pending'`; resumes after approve/reject |
| Partial unique constraint not available on SQLite (local dev) | Service-layer guard supplements the DB constraint |
| Bleach allowlist too strict and breaks legitimate content | Allowlist is reviewable; widen via spec update if real usage demands it |
