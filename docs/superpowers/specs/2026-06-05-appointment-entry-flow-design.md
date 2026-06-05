# Appointment-Entry Flow Polish — Design

Date: 2026-06-05
Status: Approved (design), pending implementation

## Context

Sub-project 3 of the design optimization (key-flow polish). The user does NOT
want patient self-booking for now — the core operation is a **doctor/admin
entering an appointment** via the "新建预约" (New Appointment) dialog.

That dialog is currently friction-heavy: the time is a flat `<ElSelect>` of
all slot times with a separate text "hint list" beside it to read availability;
there is no date picker (date is fixed to today via the form default); and a
logged-in doctor must pick themselves from a doctor dropdown.

**Key finding:** the data layer already does the hard part. In
`useAppointmentsPage.ts`, `slotOptions` is a computed that depends on
`form.doctor` + `form.date` and already yields, per slot time, `{ time, blocked,
booked }` derived from the loaded `scheduleSlots` (`isBlocked`) and existing
appointments (`bookedCount`). So this is a **frontend UI refactor only** — no
backend, API, or data-shape change.

## Goal

Make appointment entry obvious: pick patient → (doctor) → **date** → click an
available **time slot** from a visual grid that shows available / booked /
unavailable at a glance → reason → submit.

## Scope

- `features/appointments/components/CreateAppointmentDialog.vue` — add a date
  picker; replace the flat time select + hint list with a visual slot grid.
- `features/appointments/composables/useAppointmentsPage.ts` — default
  `form.doctor` to the logged-in doctor; keep `slotOptions` (already correct),
  optionally enrich each slot with a `state: 'available' | 'booked' |
  'unavailable'` derived from existing `blocked`/`booked` to simplify the view.
- i18n: new keys for the date label and slot states / empty state.

**Not in scope:** patient self-booking, records-entry dialog, scheduling page,
any backend change.

## Design

### Doctor field (role-aware)
- **Doctor logged in:** default `form.doctor = authStore.user.id` and render the
  field locked/read-only showing their own name (no dropdown). They are entering
  an appointment for a patient into their own schedule.
- **Admin:** keep the doctor `<ElSelect>`; changing it recomputes the slot grid.

### Date
- An `<ElDatePicker>` bound to `form.date` (default today). Changing it
  recomputes the grid (`slotOptions` already reacts to `form.date`).

### Slot grid (replaces flat select + hint list)
- Render `slotOptions` as a responsive grid of chips, one per slot time. State:
  - **available** (`!blocked && booked === 0`): selectable; clicking sets
    `form.time`; the chosen chip is highlighted (brand fill).
  - **booked** (`booked > 0`): disabled; label shows the time + "已约" (Booked).
  - **unavailable** (`blocked`): disabled; label shows the time + "停诊"
    (Off / unavailable), visually muted.
- Uses the Calm Clinical tokens (brand for selected, status tokens for
  booked/unavailable) for consistency with sub-project 2.
- **Empty state:** if `form.doctor` + `form.date` are set but every slot is
  unavailable/none exists, show "该日无可约时段,请先在排班开放时段。"
- Submit stays disabled until patient + doctor + time are chosen (existing
  `createSubmitAttempted` validation pattern, applied to the grid selection).

### Data
No change. `slotOptions`, `bookedCount`, `isBlocked`, `scheduleSlots`,
`patients`, `doctors` already exist in `useAppointmentsPage`. The dialog
continues to receive `patients`, `doctors`, `slotOptions` as props (plus the
new date binding); the composable just defaults the doctor.

## i18n
Add to the `appointments` locale fragment (en + zh): `dateLabel` ("Date"/"日期"),
`slotAvailable` (none/clickable — may not need a label), `slotBooked`
("Booked"/"已约"), `slotUnavailable` ("Off"/"停诊"), `noSlotsForDay`
("No bookable slots for this day — open slots in the schedule first."/
"该日无可约时段,请先在排班开放时段。"), `pickSlot` ("Pick a time slot"/"选择时段").
Reuse existing `appointments.colDoctor`, `selectPatient`, etc.

## Testing
- `vue-tsc -b --noEmit` clean; `vitest run` green (appointments composable test
  unaffected; if `slotOptions` shape gains a `state` field, update any assertion).
- Playwright: as a doctor and as an admin, open New Appointment, pick a date,
  confirm the slot grid shows available/booked/unavailable correctly and
  selecting a slot + patient submits. Both locales; 0 missing i18n keys.

## Out of scope / later
Records-entry templates, schedule bulk operations — not this sub-project.
