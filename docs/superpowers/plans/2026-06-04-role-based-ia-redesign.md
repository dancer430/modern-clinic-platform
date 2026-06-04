# Role-Based IA Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the console into role-specific navigation and merge a doctor's account + public profile (with profile review folded in) into one "医生" feature.

**Architecture:** Frontend-only IA change (Vue 3 + TS + Element Plus + vue-i18n) over existing backend APIs. Tighten per-route role gating; render navigation per role; combine `DoctorsPage` (account CRUD via `/api/auth/doctors/`) and the admin doctor-profile pages (`adminDoctorProfilesApi`, `/api/admin/content/...`) into a list + tabbed detail. No DB migration.

**Tech Stack:** Vue 3 `<script setup>`, vue-router, Pinia auth store, Element Plus, vue-i18n (locale fragments), vitest.

Spec: `docs/superpowers/specs/2026-06-04-role-based-ia-redesign-design.md`

---

## File structure

- `src/router/index.ts` — role constants, route `roles` metas, new patient routes, retire old doctor-profile/review routes (redirects).
- `src/App.vue` — role-based nav items + role-aware labels.
- `src/i18n/locales/en.ts` / `zh.ts` — `nav`, `pageTitle`, `role` keys.
- `src/views/DoctorsPage.vue` — becomes the **merged admin Doctors list** (account + profile-status columns, 待审核 filter).
- `src/features/content/pages/admin/DoctorDetailPage.vue` *(new)* — tabbed detail: 账号信息 + 公开主页 + review.
- Retire (route-level): `AdminDoctorProfileList.vue`, `AdminPendingReviews.vue` menu entries; `AdminDoctorProfileEdit.vue` logic moves into the 公开主页 tab.
- `src/features/appointments/pages/AppointmentsPage.vue` — role-aware page title.
- `src/views/PatientHomePage.vue` *(new)* — patient home.
- `src/router/__tests__/guard.spec.ts` — extend for tightened gating.

---

### Task 1: Role constants + tightened route gating

**Files:**
- Modify: `src/router/index.ts`
- Test: `src/router/__tests__/guard.spec.ts`

- [ ] **Step 1: Add a failing guard test for tightened gating**

In `src/router/__tests__/guard.spec.ts`, add:

```ts
it('blocks a patient from the admin doctors page', () => {
  const auth = useAuthStore()
  auth.user = { id: 9, username: 'p', email: 'p', name: 'P', user_type: 'patient', phone: '' }
  const next = vi.fn()
  beforeEachGuard(
    buildRoute('/doctors', { requiresAuth: true, roles: ['admin'] }),
    buildRoute('/dashboard'),
    next,
  )
  expect(next).toHaveBeenCalledWith('/dashboard')
})
```

- [ ] **Step 2: Run it; expect FAIL**

Run: `cd frontend && npx vitest run src/router/__tests__/guard.spec.ts`
Expected: FAIL (route `/doctors` currently allows all roles, but the test builds the route meta itself so it passes already — if it passes, the test documents intent; proceed to tighten real routes in Step 3).

- [ ] **Step 3: Define role groups and tighten metas**

In `src/router/index.ts` replace the constants block:

```ts
const ROLES_ALL: Array<Role> = ['admin', 'doctor', 'patient']
const ROLES_STAFF: Array<Role> = ['admin', 'doctor']
const ROLES_ADMIN: Array<Role> = ['admin']
const ROLES_DOCTOR: Array<Role> = ['doctor']
const ROLES_PATIENT: Array<Role> = ['patient']
```

Change metas:
- `/doctors` → `roles: ROLES_ADMIN`
- `/patients` → `roles: ROLES_ADMIN`
- `/appointments` → `roles: ROLES_ALL` (unchanged)
- `/timeslots`, `/records` → `roles: ROLES_STAFF` (unchanged)
- `/dashboard`, `/profile` → `roles: ROLES_ALL` (unchanged)

- [ ] **Step 4: Run guard tests; expect PASS**

Run: `cd frontend && npx vitest run src/router/__tests__/guard.spec.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/router/__tests__/guard.spec.ts
git commit -m "feat(router): tighten role gating for doctors/patients pages"
```

---

### Task 2: Patient routes + retire old doctor-profile/review routes

**Files:**
- Modify: `src/router/index.ts`
- Create: `src/views/PatientHomePage.vue` (placeholder now; real content in Task 7)

- [ ] **Step 1: Add patient home placeholder component**

Create `src/views/PatientHomePage.vue`:

```vue
<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
  <div class="page">
    <h2>{{ t('patientHome.title') }}</h2>
    <p>{{ t('patientHome.subtitle') }}</p>
  </div>
</template>
```

- [ ] **Step 2: Add routes and redirects in `src/router/index.ts`**

Add inside `routes`:

```ts
{
  path: '/home',
  name: 'patient-home',
  component: () => import('@/views/PatientHomePage.vue'),
  meta: { requiresAuth: true, roles: ['patient'] },
},
{
  path: '/doctors/:id',
  name: 'doctor-detail',
  component: () => import('@/features/content/pages/admin/DoctorDetailPage.vue'),
  meta: { requiresAuth: true, roles: ['admin'] },
},
// Retire old menu destinations -> redirect into the merged Doctors feature
{ path: '/admin/doctor-profiles', redirect: '/doctors' },
{ path: '/admin/doctor-profiles/:userId', redirect: (to) => `/doctors/${to.params.userId}` },
{ path: '/admin/reviews', redirect: '/doctors' },
```

Remove the three old named routes (`admin-doctor-profile-list`, `admin-doctor-profile-edit`, `admin-pending-reviews`) — replaced by the redirects above. Keep the `DoctorDetailPage.vue` import resolving (created in Task 6; if executing in order, create an empty stub component first so the build passes, then flesh out in Task 6).

- [ ] **Step 3: Typecheck**

Run: `cd frontend && npx vue-tsc -b --noEmit`
Expected: PASS (with a minimal `DoctorDetailPage.vue` stub present).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/views/PatientHomePage.vue
git commit -m "feat(router): add patient home + redirect retired doctor-profile/review routes"
```

---

### Task 3: Role-based navigation in App.vue

**Files:**
- Modify: `src/App.vue`

- [ ] **Step 1: Replace navItems with role-aware definition**

In `App.vue` script, replace the `navItems` array and `visibleNavItems` computed:

```ts
interface NavItem {
  path: string
  labelKey: string
  icon: unknown
  roles: Array<Role>
}

const navItems: Array<NavItem> = [
  // Admin
  { path: '/dashboard', labelKey: 'nav.dashboard', icon: DataLine, roles: ['admin', 'doctor'] },
  { path: '/home', labelKey: 'nav.home', icon: DataLine, roles: ['patient'] },
  { path: '/appointments', labelKey: 'nav.appointments', icon: Calendar, roles: ['admin'] },
  { path: '/appointments', labelKey: 'nav.myAppointments', icon: Calendar, roles: ['doctor', 'patient'] },
  { path: '/portal/doctors', labelKey: 'nav.findDoctor', icon: FirstAidKit, roles: ['patient'] },
  { path: '/doctors', labelKey: 'nav.doctors', icon: FirstAidKit, roles: ['admin'] },
  { path: '/patients', labelKey: 'nav.patients', icon: User, roles: ['admin'] },
  { path: '/timeslots', labelKey: 'nav.schedule', icon: Timer, roles: ['doctor'] },
  { path: '/records', labelKey: 'nav.records', icon: Notebook, roles: ['admin', 'doctor'] },
  { path: '/admin/departments', labelKey: 'nav.departments', icon: OfficeBuilding, roles: ['admin'] },
  { path: '/doctor/profile', labelKey: 'nav.myPublicProfile', icon: Edit, roles: ['doctor'] },
  { path: '/profile', labelKey: 'nav.profile', icon: Setting, roles: ['admin', 'doctor', 'patient'] },
]

const visibleNavItems = computed(() => {
  const role = authStore.user?.user_type
  if (!role) return []
  return navItems.filter((item) => item.roles.includes(role))
})
```

Import `Setting` from `@element-plus/icons-vue` (add to the existing icon import line). Note the two `/appointments` entries with different `labelKey` per role — the role filter guarantees only one is visible.

- [ ] **Step 2: Verify the footer profile entry**

The sidebar footer already links to `/profile`; keep it. The new `nav.profile` item gives an explicit menu row too — acceptable, or remove the footer click if redundant (leave as-is for this task).

- [ ] **Step 3: Typecheck + run app, screenshot each role's nav**

Run: `cd frontend && npx vue-tsc -b --noEmit` (expect PASS).
Drive the running dev app with Playwright for each role and confirm the nav matches the spec (admin/doctor/patient).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat(shell): role-based sidebar navigation"
```

---

### Task 4: i18n nav / pageTitle / new namespaces

**Files:**
- Modify: `src/i18n/locales/en.ts`, `src/i18n/locales/zh.ts`

- [ ] **Step 1: Add nav keys (en)**

In `en.ts` `nav`, add: `home: 'Home'`, `myAppointments: 'My Appointments'`, `findDoctor: 'Find a doctor'`, `profile: 'Profile'`. Keep existing `dashboard/doctors/patients/appointments/schedule/records/departments/myPublicProfile`. Remove now-unused `doctorProfiles`, `pendingReviews` (optional — harmless to keep).

Add a `patientHome` namespace (en): `{ title: 'Home', subtitle: 'Your upcoming appointments.' }`.

- [ ] **Step 2: Add the same keys (zh)**

`nav` (zh): `home: '首页'`, `myAppointments: '我的预约'`, `findDoctor: '找医生 · 科室'`, `profile: '个人中心'`.
`patientHome` (zh): `{ title: '首页', subtitle: '你的近期预约。' }`.

- [ ] **Step 3: pageTitle entries**

Add `'patient-home'` and `'doctor-detail'` to the `pageTitle` map in both files (en: 'Home' / 'Doctor'; zh: '首页' / '医生').

- [ ] **Step 4: Typecheck + commit**

Run: `cd frontend && npx vue-tsc -b --noEmit` (PASS).

```bash
git add frontend/src/i18n
git commit -m "feat(i18n): nav + patientHome strings for role-based IA"
```

---

### Task 5: Merged Doctors list (admin)

**Files:**
- Modify: `src/views/DoctorsPage.vue`
- Reference data: `adminDoctorProfilesApi.list()` (`src/features/content/api/doctor-profiles.ts`) returns `DoctorProfileAdmin[]` (user_id, name, title, specialty, departments, draft_status, is_published); account list from `GET /api/auth/doctors/`.

- [ ] **Step 1: Load combined rows**

In `DoctorsPage.vue`, fetch accounts (existing) and `adminDoctorProfilesApi.list()`, and build rows keyed by user id with: `name`, `title`, `specialty`, `departments`, and a derived `profileStatus`:

```ts
type ProfileStatus = 'published' | 'pending' | 'draft' | 'rejected' | 'none'
function deriveStatus(p?: DoctorProfileAdmin): ProfileStatus {
  if (!p) return 'none'
  if (p.draft_status === 'pending') return 'pending'
  if (p.is_published) return 'published'
  if (p.draft_status === 'rejected') return 'rejected'
  return p.title || p.specialty ? 'draft' : 'none'
}
```

- [ ] **Step 2: Add the 待审核 filter + status column**

Add a toolbar segmented control 全部 / 待审核 (count = rows with `pending`), filtering the table; add a `主页状态` column rendering a colored tag via `t('doctorStatus.' + status)` (add `doctorStatus` keys: published/pending/draft/rejected/none in both locales). Row "编辑" → `router.push('/doctors/' + row.id)`.

- [ ] **Step 3: Keep + reuse the existing create/edit account dialog** for `+ 新增医生` (existing DoctorsPage flow), but row-level edit now navigates to the detail page (Task 6) instead of opening the inline dialog.

- [ ] **Step 4: Typecheck + Playwright screenshot (admin, zh + en)**; confirm list shows status + filter.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/DoctorsPage.vue frontend/src/i18n
git commit -m "feat(doctors): merged list with profile status + pending-review filter"
```

---

### Task 6: Doctor detail with 账号信息 / 公开主页 tabs + review

**Files:**
- Create: `src/features/content/pages/admin/DoctorDetailPage.vue`
- Reuse: account form fields from the old `DoctorsPage` dialog; public-profile fields + `adminDoctorProfilesApi.update/setDepartments/approve/reject` from `AdminDoctorProfileEdit.vue`.

- [ ] **Step 1: Build the tabbed shell**

`DoctorDetailPage.vue`: read `:id` param; header shows the doctor's name; `<el-tabs>` with two panes:
- **账号信息** — name/email/phone/active + reset-password (PATCH `/api/auth/doctors/:id/`).
- **公开主页** — title/specialty/departments/bio (`RichTextEditor`), `保存` → `adminDoctorProfilesApi.update` + `setDepartments`. **No "save draft".** When `draft_status === 'pending'`, show a review card with `通过并发布` → `approve(id)` and `驳回` → prompt note → `reject(id, note)`.

- [ ] **Step 2: Port the public-profile logic** verbatim from `AdminDoctorProfileEdit.vue` (it already calls update/approve/reject), dropping any draft-save affordance.

- [ ] **Step 3: Delete `AdminDoctorProfileEdit.vue` / `AdminDoctorProfileList.vue` / `AdminPendingReviews.vue`** once their logic is covered (routes already redirect). Remove their locale fragment keys if now unused (optional).

- [ ] **Step 4: Typecheck + Playwright** — open `/doctors/<id>`, verify both tabs and the review card on a pending doctor.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/content/pages/admin/DoctorDetailPage.vue frontend/src/router/index.ts
git rm frontend/src/features/content/pages/admin/AdminDoctorProfile*.vue frontend/src/features/content/pages/admin/AdminPendingReviews.vue
git commit -m "feat(doctors): tabbed account+profile detail with inline review"
```

---

### Task 7: Appointments role-aware title + Patient Home content

**Files:**
- Modify: `src/features/appointments/pages/AppointmentsPage.vue`
- Modify: `src/views/PatientHomePage.vue`

- [ ] **Step 1: Role-aware appointments title**

In `AppointmentsPage.vue`, compute the title from the auth role: admin → `t('appointments.titleManage')` (= existing "Appointments"/"预约管理"), doctor/patient → `t('appointments.titleMine')` (= "My Appointments"/"我的预约"). Add those two keys; keep the existing `appointments.title` usage pointing at the computed value.

- [ ] **Step 2: Patient Home content**

Fill `PatientHomePage.vue`: fetch the patient's appointments (`GET /api/appointments/` — backend already scopes by role) and show upcoming ones as cards + a `预约` button linking to `/portal/doctors`. Reuse the dashboard card styling.

- [ ] **Step 3: Typecheck + Playwright (patient login)** — confirm Home renders and 预约 nav works.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/appointments/pages/AppointmentsPage.vue frontend/src/views/PatientHomePage.vue frontend/src/i18n
git commit -m "feat(appointments,patient): role-aware title + patient home"
```

---

### Task 8: Full verification

- [ ] **Step 1: Typecheck** — `cd frontend && npx vue-tsc -b --noEmit` → PASS.
- [ ] **Step 2: Unit tests** — `cd frontend && npx vitest run` → all green (guard test updated).
- [ ] **Step 3: Playwright sweep** — for each role (admin via `.deploy-credentials`, doctor `doctor_test/Demo@12345`, create/seed a patient), in both zh+en: confirm nav, the merged Doctors list + detail + review, appointments title, patient home. Capture screenshots; confirm **0 missing i18n keys** in console.
- [ ] **Step 4: Commit any test fixups.**

---

## Notes for the executor

- Backend is unchanged; everything uses existing endpoints. If the admin Doctors list join (accounts × profiles) is awkward, it is acceptable to render from `adminDoctorProfilesApi.list()` alone (it already carries name/title/specialty/departments/status) and reach account fields lazily in the detail page.
- Keep English i18n values identical to any pre-existing strings being reused so existing tests stay green.
- This plan is **frontend-only** and additive at the API layer; no migration, no backend deploy needed beyond the standard `service-update` to publish the new frontend.
