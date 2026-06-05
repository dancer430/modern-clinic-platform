# Appointment-Entry Flow Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the doctor/admin "New Appointment" dialog effortless: a visual slot grid (available/booked/off) replacing the flat time dropdown + hint list, and a role-aware doctor field (locked to self for doctors).

**Architecture:** Frontend-only. The composable `useAppointmentsPage.ts` already computes per-slot `{ time, blocked, booked }` from `scheduleSlots` + appointments, reactive to `form.doctor`+`form.date`. We enrich it with a `state` field, default the doctor to the logged-in doctor, and rewrite the dialog's slot UI. No backend/API/data change.

**Tech Stack:** Vue 3 `<script setup>`, Element Plus, vue-i18n, Pinia auth, vitest.

Spec: `docs/superpowers/specs/2026-06-05-appointment-entry-flow-design.md`

---

## File structure
- `src/features/appointments/composables/useAppointmentsPage.ts` — default doctor to self on open; add `state` to `slotOptions`.
- `src/features/appointments/components/CreateAppointmentDialog.vue` — visual slot grid; role-aware doctor field; empty state. (Already has the date picker.)
- `src/i18n/locales/fragments/appointments.ts` — new keys.

---

### Task 1: Composable — default doctor to self + slotOptions.state

**Files:** Modify `src/features/appointments/composables/useAppointmentsPage.ts`. Test: `src/features/appointments/__tests__/useAppointmentsPage.spec.ts`.

- [ ] **Step 1: Enrich `slotOptions` with a `state` field.** Find the `slotOptions` computed. Change the returned object to add `state`:

```ts
const slotOptions = computed(() => {
  if (!form.value.doctor || !form.value.date) return []
  return SLOT_TIMES.map((time) => {
    const blocked = isBlocked(form.value.doctor as number, form.value.date, time)
    const booked = bookedCount(form.value.doctor as number, form.value.date, time)
    const state: 'available' | 'booked' | 'unavailable' =
      blocked ? 'unavailable' : booked > 0 ? 'booked' : 'available'
    return {
      time,
      blocked,
      booked,
      state,
      label: blocked ? `${time} · unavailable` : `${time} · ${booked} booked`,
    }
  })
})
```

- [ ] **Step 2: Default the doctor to the logged-in doctor when the dialog opens.** At the top of the composable, import the auth store: `import { useAuthStore } from '@/features/auth'` and (inside the composable function) `const authStore = useAuthStore()`. Find `openCreate` (it resets the form). After it resets `form.value` (e.g. `form.value = createDefaultForm()`), set the doctor for doctor-role users:

```ts
const openCreate = () => {
  form.value = createDefaultForm()
  if (authStore.user?.user_type === 'doctor') {
    form.value.doctor = authStore.user.id
  }
  createSubmitAttempted.value = false   // keep whatever reset lines already exist
  createDialogVisible.value = true      // keep the existing visibility flag name
}
```
(READ the existing `openCreate` first and preserve its exact reset lines / flag names; only ADD the doctor-default block.)

- [ ] **Step 3: Update the composable test if needed.** Run `cd frontend && npx vitest run src/features/appointments/__tests__/useAppointmentsPage.spec.ts`. If it asserts the `slotOptions` shape, update those assertions to include `state` (the existing fields stay). If it doesn't touch `slotOptions`, no change. Re-run → PASS.

- [ ] **Step 4: Typecheck + commit**

Run `cd frontend && npx vue-tsc -b --noEmit` (clean).

```bash
git add frontend/src/features/appointments/composables/useAppointmentsPage.ts frontend/src/features/appointments/__tests__/useAppointmentsPage.spec.ts
git commit -m "feat(appointments): slot state + default doctor to self in new-appointment form"
```

---

### Task 2: i18n keys

**Files:** Modify `src/i18n/locales/fragments/appointments.ts` (it exports `en` and `zh` with an `appointments` namespace).

- [ ] **Step 1: Add keys to BOTH en and zh** under `appointments`:

en:
```
slotBooked: 'Booked',
slotOff: 'Off',
pickSlot: 'Pick a time slot',
noSlotsForDay: 'No bookable slots for this day — open slots in the schedule first.',
selectDoctorFirst: 'Select a doctor and date to see available slots.',
```
zh:
```
slotBooked: '已约',
slotOff: '停诊',
pickSlot: '选择时段',
noSlotsForDay: '该日无可约时段,请先在排班开放时段。',
selectDoctorFirst: '请先选择医生和日期以查看可约时段。',
```
Keep existing `appointments.*` keys (e.g. `timeSlot`, `bookedCount`, `unavailableBySchedule`, `bookedCountHint`) — they may stay referenced or become unused (harmless).

- [ ] **Step 2: Typecheck + commit**

Run `cd frontend && npx vue-tsc -b --noEmit` (clean); `npx vitest run` (green).

```bash
git add frontend/src/i18n/locales/fragments/appointments.ts
git commit -m "feat(i18n): appointment slot-grid strings"
```

---

### Task 3: Dialog — visual slot grid + role-aware doctor field

**Files:** Modify `src/features/appointments/components/CreateAppointmentDialog.vue`.

- [ ] **Step 1: Update the `slotOptions` prop type** in `defineProps` to include `state`:
```ts
slotOptions: Array<{ time: string; blocked: boolean; booked: number; state: 'available' | 'booked' | 'unavailable'; label: string }>
```

- [ ] **Step 2: Make the doctor field role-aware.** Add to `<script setup>`: `import { useAuthStore } from '@/features/auth'` and `import { computed } from 'vue'`, then:
```ts
const authStore = useAuthStore()
const isDoctorSelf = computed(() => authStore.user?.user_type === 'doctor')
const selfName = computed(() => authStore.user?.name || authStore.user?.username || '')
```
In the template, replace the doctor `<ElFormItem>`'s `<ElSelect>` with a role-aware block (keep the same `:label="t('appointments.colDoctor')"`):
```vue
<ElFormItem :label="t('appointments.colDoctor')" required>
  <div v-if="isDoctorSelf" class="locked-field">{{ selfName }}</div>
  <ElSelect
    v-else
    v-model="form.doctor"
    :placeholder="t('appointments.selectDoctor')"
    style="width: 100%;"
    :class="{ 'is-error': createSubmitAttempted && !form.doctor }"
  >
    <ElOption v-for="doctor in doctors" :key="doctor.id" :label="displayName(doctor)" :value="doctor.id" />
  </ElSelect>
</ElFormItem>
```

- [ ] **Step 3: Replace the time `<ElSelect>` ElFormItem AND the `.slot-hint-card` block with a slot grid.** Replace the `timeSlot` `<ElFormItem>` (the one with the time `<ElSelect>`) and DELETE the entire `<div class="slot-hint-card">…</div>` below the form. New form item:
```vue
<ElFormItem :label="t('appointments.pickSlot')" required>
  <div class="slot-grid" :class="{ 'is-error': createSubmitAttempted && !form.time }">
    <template v-if="slotOptions.length">
      <button
        v-for="slot in slotOptions"
        :key="slot.time"
        type="button"
        class="slot-chip"
        :class="[`slot-chip--${slot.state}`, { 'slot-chip--selected': form.time === slot.time }]"
        :disabled="slot.state !== 'available'"
        @click="form.time = slot.time"
      >
        <span class="slot-chip__time">{{ slot.time }}</span>
        <span v-if="slot.state === 'booked'" class="slot-chip__tag">{{ t('appointments.slotBooked') }}</span>
        <span v-else-if="slot.state === 'unavailable'" class="slot-chip__tag">{{ t('appointments.slotOff') }}</span>
      </button>
    </template>
    <p v-else class="slot-empty">{{ form.doctor && form.date ? t('appointments.noSlotsForDay') : t('appointments.selectDoctorFirst') }}</p>
  </div>
</ElFormItem>
```
(Note: when no slot is `available` but some exist, the grid still shows them all disabled — that's fine; `slotOptions.length` is only 0 when doctor/date unset. To also catch "all unavailable", you may show `noSlotsForDay` when `slotOptions.length && slotOptions.every(s => s.state !== 'available')` — optional refinement, keep simple if unsure.)

- [ ] **Step 4: Add scoped styles** (Calm Clinical tokens) at the end of `<style scoped>` (and remove the now-unused `.slot-hint-card` styles):
```css
.slot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 8px; width: 100%; }
.slot-grid.is-error { outline: 1px solid var(--danger-text); outline-offset: 4px; border-radius: 8px; }
.slot-chip {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 8px 6px; border-radius: var(--radius-control, 10px);
  border: 1px solid var(--line); background: #fff; cursor: pointer;
  font-size: 13px; color: var(--primary); transition: all .15s ease;
}
.slot-chip--available:hover { border-color: var(--primary); background: var(--primary-soft); }
.slot-chip--selected { background: var(--primary); border-color: var(--primary); color: #fff; }
.slot-chip--booked { background: var(--status-pending-bg); border-color: transparent; color: var(--status-pending-text); cursor: not-allowed; }
.slot-chip--unavailable { background: var(--status-neutral-bg); border-color: transparent; color: var(--muted); cursor: not-allowed; }
.slot-chip__tag { font-size: 10px; }
.slot-empty { color: var(--muted); font-size: 13px; margin: 4px 0; }
.locked-field { height: 32px; display: flex; align-items: center; padding: 0 10px; border-radius: var(--radius-control, 10px); background: var(--primary-soft); color: var(--primary); font-size: 13px; }
```

- [ ] **Step 5: Verify + commit**

Run `cd frontend && npx vue-tsc -b --noEmit` (clean); `npx vitest run` (green).

```bash
git add frontend/src/features/appointments/components/CreateAppointmentDialog.vue
git commit -m "feat(appointments): visual slot grid + role-aware doctor in new-appointment dialog"
```

---

### Task 4: Verification

- [ ] **Step 1: Typecheck + tests** — `cd frontend && npx vue-tsc -b --noEmit` clean; `npx vitest run` green.
- [ ] **Step 2: Playwright** — start the dev server. As **doctor_test** and as **admin** (both locales), open Appointments → New Appointment:
  - Doctor: the doctor field shows their own name locked (no dropdown); pick a date; the slot grid shows available chips (clickable, selectable→highlight), booked chips ("已约", disabled), off chips ("停诊", disabled). Select a patient + slot, submit → appointment created.
  - Admin: doctor is a dropdown; changing doctor/date refreshes the grid.
  - Confirm empty state text when no doctor/date or no slots. 0 missing i18n keys.
- [ ] **Step 3: Commit any fixups.**

---

## Notes for the executor
- Frontend-only; no backend/data change. `slotOptions`/`bookedCount`/`isBlocked` already exist.
- Keep existing i18n keys; only add. Don't change the records-entry dialog or schedule page.
- After merge, deploy to the demo via `service-update` from a fresh `main` worktree.
