# Appointments Management Enhancements + Operations Role — Design

Date: 2026-06-05
Status: Approved (design), pending implementation

## Context & goal

Improve the appointments-management area: clearer status wording, a richer
filter bar, an appointment detail view exposing contact info, and a new
read-only **Operations** role (e.g. front-desk / scheduling nurse) who can see
the schedule and patient/doctor contact details to proactively call patients,
but cannot make any change.

## Scope (this sub-project)
A. Appointment status relabel (frontend i18n only).
B. New read-only **Operations** role (backend RBAC + frontend nav/guards/UI).
C. Appointment **detail drawer** + contact fields (backend serializer, role-gated).
D. Clearer **filter bar** (frontend; backend already supports the params).

Not in scope: records-entry, scheduling pages, patient self-booking.

## A. Status relabel

Display text only — the underlying status keys (`pending/confirmed/completed/
cancelled`) DO NOT change. Update the `status` i18n namespace:

| key | en | zh |
|---|---|---|
| pending | Pending | 待就诊 |
| confirmed | Consulting | 诊疗中 |
| completed | Completed (unchanged) | 已完成 |
| cancelled | Cancelled (unchanged) | 已取消 |

Action buttons unchanged ("确认" / "完成就诊" / "取消"). Flow reads:
待就诊 →(确认)→ 诊疗中 →(完成就诊)→ 已完成. "未就诊" = the `pending`
(待就诊) status; no new status or marker.

## B. Operations role (read-only)

### Backend
- `users/models.py` `User.Role`: add `OPERATOR = "operator", "Operations"`.
  This is a `TextChoices` change → Django generates a **no-op `AlterField`
  migration** (validation metadata only; no DB schema change). Non-destructive.
- Appointment access (`appointments/views.py`):
  - `get_queryset`: an operator sees **all** appointments (same branch as admin;
    no doctor/patient narrowing).
  - Mutations — create, `confirm`, `complete`, `cancel`, and any update — must be
    rejected for operator (and remain disallowed for patient). Implement a
    permission/guard so non-staff (anyone who is not admin or doctor) gets `403`
    on those actions; operator keeps `list`/`retrieve`.
- Seed a demo operator account (e.g. `ops_test` / `Demo@12345`, role `operator`)
  in the demo-seed script, local and server.

### Frontend
- Add `'operator'` to the `Role` union (`features/auth/types`).
- Navigation (`App.vue`): operator sees **工作台 · 预约管理 · 个人中心** only.
- Route guards (`router/index.ts`): operator allowed on `/dashboard`,
  `/appointments`, `/profile`; blocked from doctors/patients/timeslots/records/
  admin. Post-login landing: operator → `/dashboard` (today overview).
- Read-only enforcement in UI:
  - `DashboardPage`: hide the "Quick Actions" panel for operator (those are
    staff manage-links). The today-schedule + status distribution stay.
  - `AppointmentsPage` / `AppointmentsTableCard`: for operator, hide the
    `+ 新建预约` button and the row Actions buttons (确认/完成就诊/取消). Operator
    can still open the detail drawer (read-only).
  - Page title for operator = "预约管理" (same as admin's manage view).

## C. Appointment detail drawer + contact fields

### Backend (`appointments/serializers.py`)
Add four contact fields to `AppointmentSerializer`, each a
`SerializerMethodField` that returns the value **only when the requesting user's
role is admin, doctor, or operator** (else empty string), using the serializer's
`request` context:
- `patient_phone`, `patient_email` (from `obj.patient.phone` / `.email`)
- `doctor_phone`, `doctor_email` (from `obj.doctor.phone` / `.email`)
Add them to `fields`. (Patients only ever list their own appointments, and these
fields are blanked for the patient role anyway.)

### Frontend
- A new `AppointmentDetailDrawer.vue` (`features/appointments/components/`)
  using `<el-drawer>`: header with `StatusBadge`; sections for **患者**
  (name + phone + email), **医生** (name + phone + email), **日期时间**,
  **就诊原因**, and — when status is `completed` — 诊断结论 / 治疗方案 / 医嘱.
- Open it from the appointments table: clicking a row (or a "详情" action)
  sets the selected appointment and opens the drawer. Read-only for everyone
  (it's a view; existing mutation buttons stay in the row/their dialogs).
- i18n: add keys for the drawer labels (detail title, patient/doctor contact
  labels, phone/email, "未填写" fallback) in en + zh.

## D. Filter bar (frontend)

Rework `AppointmentsFilters.vue` into a clearer bar:
- **Name search** (one input; matches patient OR doctor name) → existing `q`
  param.
- **Status** select (existing) — options use the relabeled status text.
- **Date** picker → the `date` query param (backend already filters
  `appointment_date=date`).
- **搜索 / 重置** buttons; a **今日 (Today)** quick button that sets date=today
  and searches.
- Backend support already exists (`status`, `q`, `date`, `date_from/to`); no
  backend filter change needed beyond what B/C add.

## Data / migration
- One migration: `users` `AlterField` for `role` choices (adds `operator`).
  No data backfill, no schema change. Safe.

## Testing
- Backend: pytest — operator can list/retrieve appointments but gets 403 on
  create/confirm/complete/cancel; contact fields present for admin/doctor/
  operator and blank for patient. Existing suite stays green.
- Frontend: `vue-tsc -b --noEmit` clean; `vitest run` green (StatusBadge text
  test still passes — en `pending` stays "Pending"; if any test asserts
  "Confirmed", update to "Consulting"). Extend the router guard test for
  operator gating.
- Playwright: operator login → read-only appointments (no action buttons / no
  new-appointment), detail drawer shows contact info, filter bar (name/status/
  date/today) works; staff see contact info in the drawer; both locales; 0
  missing i18n keys.

## Out of scope / later
Records-entry templates, schedule bulk ops, patient self-booking.
