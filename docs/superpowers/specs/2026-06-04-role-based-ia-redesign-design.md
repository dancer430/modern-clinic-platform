# Role-Based Information Architecture Redesign — Design

Date: 2026-06-04
Status: Approved (design), pending implementation

## Context

The console grew an inconsistent navigation: management pages (Doctors,
Patients) are visible to all roles including patients; a doctor's data is
split across two menus ("医生" = accounts, "医生主页" = public profile); and
there is no "personal vs management" structure. The user asked to optimize
the overall design, not limited to the current implementation.

This is the **first of three** decomposed sub-projects:

1. **IA + role-based navigation + Doctors merge** (this spec) — the backbone.
2. Visual design system (colors, components, spacing, status styling) — later.
3. Key-flow polish (booking, scheduling, records entry) — later.

Only sub-project 1 is specified here.

## Goals

- A distinct, purpose-clear navigation per role (admin / doctor / patient).
- Each nav item has one clear responsibility.
- Merge a doctor's account management and public-profile management into one
  surface; fold the profile-review queue into it.
- Stop leaking management pages to roles that shouldn't see them.

## Role model

| Role | What they do here |
|---|---|
| **Admin** | Manage doctors (accounts + public profiles), patients, departments, all appointments; review doctor-profile drafts; platform branding. |
| **Doctor** | See their own appointments, manage their own schedule, write medical records, edit their own public profile (draft → submit for review). |
| **Patient** | Browse departments/doctors, book and view their own appointments, manage their own account. |

## Target navigation (role-based)

**Admin**
- 工作台 (Dashboard) — global today overview + key stats
- 预约管理 (Appointments) — all doctors' appointments
- 医生 (Doctors) — **merged** list; entry → account info + public profile in one place (absorbs the old "医生主页"); review queue folded in via a "待审核 N" filter/badge
- 患者 (Patients) — patient account management
- 科室 (Departments) — department management
- 个人中心 (Profile) — own account + **platform branding** (admin-only section, unchanged location)

**Doctor**
- 工作台 (Dashboard) — my today overview
- 我的预约 (My Appointments) — appointments assigned to me; confirm / complete
- 我的排班 (My Schedule)
- 电子病历 (Medical Records) — records I authored
- 我的主页 (My Public Profile) — edit own profile, submit for review (keeps "save draft")
- 个人中心 (Profile)

**Patient**
- 首页 (Home) — my upcoming appointments + quick book
- 找医生 · 科室 (Find a doctor / departments) — portal browse → book
- 我的预约 (My Appointments) — my bookings; new booking
- 个人中心 (Profile)

### Decisions confirmed with the user
- **待审核** is merged into **医生** (badge + filter), not a standalone menu item.
- **Appointments page** is one page scoped by role: admin = "预约管理" (all),
  doctor/patient = "我的预约" (own only). Title differs by role.
- The admin's public-profile editor has **no "save draft"** — just Save (and
  the review actions when a draft is pending). "Save draft" remains only in
  the doctor's own "我的主页".

## "医生" merged page

**List view** — columns: 姓名, 职称, 专长, 科室, 主页状态 (已发布 / 待审核 /
未创建 / 已驳回), 操作(编辑). Toolbar: search (name/specialty), a
全部 / 待审核 N filter, and `+ 新增医生`.

**Detail / edit view** (click a doctor) — header with the doctor's name and
two tabs:
- **账号信息** — username, name, email, phone, active status, reset password
  (the current DoctorsPage account form).
- **公开主页** — title, specialty, departments, bio (rich text), publish state
  (the current AdminDoctorProfileEdit content), **minus** the draft concept on
  the admin side. When the doctor has submitted a draft pending review, a
  review card appears with **通过并发布 / 驳回(填理由)** actions.

This unifies the previous `/doctors` (account CRUD) and
`/admin/doctor-profiles[/:id]` (public profile) into one feature.

## Routing & guards

- Navigation items are filtered by the authenticated role; each route carries
  a `roles` meta and the guard redirects role mismatches (existing guard
  pattern, but applied consistently — management routes no longer use
  ROLES_ALL).
- New/changed routes:
  - `/doctors` → merged Doctors list (admin).
  - `/doctors/:id` → doctor detail with 账号信息 / 公开主页 tabs (admin).
  - Remove standalone `/admin/doctor-profiles`, `/admin/doctor-profiles/:userId`,
    `/admin/reviews` menu entries (their functionality moves into `/doctors`;
    routes may redirect or be retired).
  - Patient: ensure `/portal/*` is reachable from an in-app "找医生·科室" nav
    entry; add a patient "首页".
- The appointments route stays one component; the page title and any
  create/manage affordances adapt to role.

## Backend / data considerations

- The merged Doctors **list** needs both account fields (from
  `/api/auth/doctors/`) and public-profile summary (title, specialty,
  departments, draft_status/is_published from the content doctor-profile API).
  Implementation may either call both and join client-side, or add/extend an
  admin endpoint that returns the combined row. Prefer reusing existing
  endpoints and joining client-side first; only add an endpoint if the join is
  awkward. **No DB migration is expected** — this is a presentation/IA change
  over existing models (User, DoctorProfile, DoctorDepartment).
- Review actions (approve/reject) reuse the existing doctor-profile review
  endpoints.

## i18n impact

- Nav keys change (some items renamed/removed, new patient items). Update the
  `nav` namespace and `pageTitle` map in `src/i18n/locales/en.ts` / `zh.ts`.
- New strings for the merged Doctors detail tabs and the patient Home land in
  the relevant locale fragments. English values follow existing conventions;
  zh provided.

## Testing

- Update/extend the router guard test for the tightened role gating.
- Component tests for the merged Doctors list/detail where practical.
- `vue-tsc -b --noEmit` clean; `vitest run` green.
- Manual verification via Playwright in both locales for each role's nav.

## Out of scope (follow-up sub-projects)

- Visual design system (sub-project 2): color tokens, component/badge/table/form
  styling consistency, spacing, professional polish.
- Key-flow polish (sub-project 3): booking, scheduling, records-entry UX.
These get their own spec → plan → implementation cycles after this backbone
lands.
