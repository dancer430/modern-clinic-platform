# Appointments Management Enhancements + Operations Role — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Relabel appointment statuses, add a read-only **Operations** role, an appointment **detail drawer** with role-gated contact info, and a clearer **filter bar** (name/status/date/today).

**Architecture:** Backend = new `User.Role.OPERATOR` (no-op choices migration) + a write-guard permission + operator-sees-all queryset + role-gated contact fields on the appointment serializer. Frontend = status i18n relabel, operator role plumbing (nav/guards/read-only UI), a new detail drawer, and a date-aware filter bar. Backend list filtering (status/q/date) already exists.

**Tech Stack:** Django + DRF + pytest (backend); Vue 3 `<script setup>` + Element Plus + vue-i18n + vitest (frontend).

Spec: `docs/superpowers/specs/2026-06-05-appointments-management-enhancements-design.md`

---

## File structure
- `backend/users/models.py` (+ migration) — `Role.OPERATOR`.
- `backend/appointments/views.py` — write-guard permission; operator queryset.
- `backend/appointments/serializers.py` — role-gated contact fields.
- `backend/seed_demo_full.py` — demo operator account.
- `frontend/src/i18n/locales/...` — status relabel + operator + drawer keys.
- `frontend/src/features/auth/types/index.ts`, `src/router/index.ts`, `src/App.vue`, `src/views/DashboardPage.vue` — operator role.
- `frontend/src/features/appointments/components/AppointmentsFilters.vue`, `.../AppointmentDetailDrawer.vue` (new), `.../pages/AppointmentsPage.vue`, `.../composables/useAppointmentsPage.ts` — filters, drawer, gating.

---

### Task 1: Backend — Operations role + write-guard + queryset

**Files:** `backend/users/models.py` (+ new migration), `backend/appointments/views.py`. Test: `backend/tests/appointments/test_api_operator.py` (new).

- [ ] **Step 1: Add the role.** In `users/models.py` `class Role(models.TextChoices)` add: `OPERATOR = "operator", "Operations"` (after PATIENT).

- [ ] **Step 2: Make the migration.** Run `cd backend && .venv/bin/python manage.py makemigrations users` → creates a no-op `AlterField` for `role` choices. Then `.venv/bin/python manage.py migrate`.

- [ ] **Step 3: Write failing tests** `backend/tests/appointments/test_api_operator.py`:
```python
import pytest
from users.models import User

@pytest.mark.django_db
def test_operator_lists_all_appointments(operator_client, appointment_factory):
    appointment_factory()  # any appointment, any doctor/patient
    resp = operator_client.get("/api/appointments/")
    assert resp.status_code == 200
    assert resp.data["count"] >= 1

@pytest.mark.django_db
def test_operator_cannot_create_appointment(operator_client, doctor_user, patient_user):
    resp = operator_client.post("/api/appointments/", {
        "patient": patient_user.id, "doctor": doctor_user.id,
        "appointment_date": "2026-06-10", "appointment_time": "09:00",
    }, format="json")
    assert resp.status_code == 403

@pytest.mark.django_db
def test_operator_cannot_confirm(operator_client, pending_appointment):
    resp = operator_client.put(f"/api/appointments/{pending_appointment.id}/confirm/", {"confirm_info": "x"}, format="json")
    assert resp.status_code == 403
```
Add an `operator_client` fixture (in `tests/conftest.py` or this file) mirroring the existing `admin_client`/`doctor_client` fixtures but with a user whose `role=User.Role.OPERATOR` (READ the existing client fixtures to copy the auth pattern). Reuse existing `doctor_user`/`patient_user`/`pending_appointment`/`appointment_factory` fixtures (search `tests/` — adapt names to what exists; if `appointment_factory`/`pending_appointment` don't exist, create the appointment inline with `Appointment.objects.create(...)`).

Run: `cd backend && .venv/bin/python -m pytest tests/appointments/test_api_operator.py -q` → FAIL (operator currently falls into the patient branch → sees none; create/confirm not yet 403).

- [ ] **Step 4: Add the write-guard permission + operator queryset** in `appointments/views.py`. Add above `AppointmentViewSet`:
```python
class AppointmentAccessPermission(permissions.IsAuthenticated):
    """Read for any authenticated user; writes only for admin/doctor."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if view.action in ("list", "retrieve"):
            return True
        return request.user.role in (User.Role.ADMIN, User.Role.DOCTOR)
```
Set `permission_classes = [AppointmentAccessPermission]` on `AppointmentViewSet` (replacing `[permissions.IsAuthenticated]`). In `get_queryset`, change the final role branch so operator sees all:
```python
        if user.role in (User.Role.ADMIN, User.Role.OPERATOR):
            return queryset
        if user.role == User.Role.DOCTOR:
            return queryset.filter(doctor=user)
        return queryset.filter(patient=user)
```

- [ ] **Step 5: Run tests → PASS**, then the full backend suite `cd backend && .venv/bin/python -m pytest -q` (green).

- [ ] **Step 6: Commit**
```bash
git add backend/users/models.py backend/users/migrations/ backend/appointments/views.py backend/tests/appointments/test_api_operator.py
git commit -m "feat(rbac): read-only Operations role for appointments"
```

---

### Task 2: Backend — role-gated contact fields on appointment serializer

**Files:** `backend/appointments/serializers.py`. Test: `backend/tests/appointments/test_api_operator.py` (extend) or the existing appointment serializer test.

- [ ] **Step 1: Write failing test** (add to the operator test file):
```python
@pytest.mark.django_db
def test_contact_fields_visible_to_operator_blank_to_patient(operator_client, patient_client, doctor_user, patient_user):
    patient_user.phone = "13800001234"; patient_user.email = "p@example.com"; patient_user.save()
    doctor_user.phone = "13900005678"; doctor_user.save()
    from appointments.models import Appointment
    Appointment.objects.create(patient=patient_user, doctor=doctor_user,
        appointment_date="2026-06-10", appointment_time="09:00", created_by=patient_user)
    op = operator_client.get("/api/appointments/").data["results"][0]
    assert op["patient_phone"] == "13800001234" and op["doctor_phone"] == "13900005678"
    pt = patient_client.get("/api/appointments/").data["results"][0]
    assert pt["patient_phone"] == "" and pt["doctor_phone"] == ""
```
Run → FAIL (fields don't exist).

- [ ] **Step 2: Add the fields** to `AppointmentSerializer`. Add a role-check helper + four `SerializerMethodField`s:
```python
    patient_phone = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    doctor_phone = serializers.SerializerMethodField()
    doctor_email = serializers.SerializerMethodField()

    def _can_see_contact(self):
        request = self.context.get("request")
        role = getattr(getattr(request, "user", None), "role", None)
        from users.models import User
        return role in (User.Role.ADMIN, User.Role.DOCTOR, User.Role.OPERATOR)

    def get_patient_phone(self, obj):
        return (obj.patient.phone or "") if self._can_see_contact() else ""
    def get_patient_email(self, obj):
        return (obj.patient.email or "") if self._can_see_contact() else ""
    def get_doctor_phone(self, obj):
        return (obj.doctor.phone or "") if self._can_see_contact() else ""
    def get_doctor_email(self, obj):
        return (obj.doctor.email or "") if self._can_see_contact() else ""
```
Add `"patient_phone", "patient_email", "doctor_phone", "doctor_email"` to `Meta.fields` (after `doctor_name`). They're method fields → read-only automatically.

- [ ] **Step 3: Run tests → PASS**; full backend suite green.

- [ ] **Step 4: Commit**
```bash
git add backend/appointments/serializers.py backend/tests/appointments/test_api_operator.py
git commit -m "feat(appointments): role-gated patient/doctor contact fields"
```

---

### Task 3: Seed a demo operator account

**Files:** `backend/seed_demo_full.py`.

- [ ] **Step 1: Add an operator user.** READ `seed_demo_full.py`; near where it creates the doctor/patients with `get_or_create` + `set_password`, add:
```python
op, _ = U.objects.get_or_create(username="ops_test", defaults={"role": "operator"})
op.role = "operator"; op.name = "Front Desk"; op.email = "ops@example.com"; op.phone = "13700000000"; op.set_password(PWD); op.save()
```
(`PWD = "Demo@12345"` already defined in that script.) Print it in the summary line.

- [ ] **Step 2: Commit**
```bash
git add backend/seed_demo_full.py
git commit -m "chore(seed): demo operator account"
```

---

### Task 4: Frontend i18n — status relabel + operator + drawer keys

**Files:** `frontend/src/i18n/locales/en.ts`, `zh.ts`, and the `appointments` fragment.

- [ ] **Step 1: Relabel statuses.** In the core `status` namespace: en — set `confirmed: 'Consulting'` (keep `pending: 'Pending'`, `completed`, `cancelled`). zh — set `pending: '待就诊'`, `confirmed: '诊疗中'` (keep `completed: '已完成'`, `cancelled: '已取消'`).

- [ ] **Step 2: Role label.** In the `role` namespace add: en `operator: 'Operations'`; zh `operator: '运营'`.

- [ ] **Step 3: Nav + pageTitle.** Existing `nav.dashboard/appointments/profile` are reused for operator (no new nav keys needed). No pageTitle change.

- [ ] **Step 4: Drawer keys** in the `appointments` fragment (en + zh):
```
detailTitle:   'Appointment detail' / '预约详情'
sectionPatient:'Patient' / '患者'
sectionDoctor: 'Doctor' / '医生'
contactPhone:  'Phone' / '电话'
contactEmail:  'Email' / '邮箱'
fieldDateTime: 'Date & time' / '日期时间'
notProvided:   'Not provided' / '未填写'
viewDetail:    'Detail' / '详情'
todayFilter:   'Today' / '今日'
dateFilter:    'Date' / '日期'
```

- [ ] **Step 5: Verify + commit**. `cd frontend && npx vue-tsc -b --noEmit` clean; `npx vitest run` green (StatusBadge en `pending`='Pending' still passes; if any test asserts 'Confirmed', change to 'Consulting').
```bash
git add frontend/src/i18n
git commit -m "feat(i18n): relabel statuses (待就诊/诊疗中, Consulting) + operator/drawer strings"
```

---

### Task 5: Frontend — operator role plumbing + read-only gating

**Files:** `frontend/src/features/auth/types/index.ts`, `src/router/index.ts`, `src/App.vue`, `src/views/DashboardPage.vue`, `src/features/appointments/pages/AppointmentsPage.vue`, `.../components/AppointmentsTableCard.vue`. Test: `src/router/__tests__/guard.spec.ts`.

- [ ] **Step 1: Role union.** In `features/auth/types/index.ts` change `export type Role = 'admin' | 'doctor' | 'patient'` → add `| 'operator'`.

- [ ] **Step 2: Routes.** In `router/index.ts` add `'operator'` to the `roles` arrays of `/dashboard`, `/appointments`, and `/profile`. (Leave `/home`, `/doctors`, `/patients`, `/timeslots`, `/records`, admin routes unchanged → operator is blocked from those by the guard.) `homePathForRole` already returns `/dashboard` for non-patient → operator lands on `/dashboard`; no change needed there.

- [ ] **Step 3: Nav.** In `App.vue` `navItems`, add `'operator'` to the `roles` of the Dashboard item (`{ path: '/dashboard', labelKey: 'nav.dashboard', icon: DataLine, roles: ['admin', 'doctor', 'operator'] }`), the admin Appointments item (`roles: ['admin', 'operator']`), and the Profile item (`roles: [..., 'operator']`). Operator thus sees 工作台 · 预约管理 · 个人中心 only.

- [ ] **Step 4: Dashboard hide quick-actions for operator.** In `DashboardPage.vue`, wrap the "Quick Actions" `<section>`/panel in `v-if="!isOperator"` where `const isOperator = computed(() => authStore.user?.user_type === 'operator')` (import `useAuthStore`). Keep the stats + today-schedule + status distribution.

- [ ] **Step 5: Read-only gating in appointments.** In `AppointmentsPage.vue`, add `const canManage = computed(() => authStore.isAdmin || authStore.isDoctor)` and: gate the `+ 新建预约` `<ElButton>` with `v-if="canManage"`. Pass `:can-manage="canManage"` to `AppointmentsTableCard`. In `AppointmentsTableCard.vue`, add `canManage: boolean` to `defineProps`, and wrap the cancel button (and the whole actions cell content for pending/confirmed) so action buttons only render `v-if="canManage"`. (Confirm/Complete already gate on `canConfirm`/`canComplete` = admin/doctor-owner, so they're already hidden for operator; the cancel button needs the `canManage` guard.)

- [ ] **Step 6: Guard test.** In `guard.spec.ts` add a test that an operator is allowed on `/appointments` (meta roles include `'operator'`) and blocked from `/doctors` (redirected). Follow existing test shape.

- [ ] **Step 7: Verify + commit.** `npx vue-tsc -b --noEmit` clean; `npx vitest run` green.
```bash
git add frontend/src/features/auth frontend/src/router frontend/src/App.vue frontend/src/views/DashboardPage.vue frontend/src/features/appointments
git commit -m "feat(operator): role nav/guards + read-only appointments + dashboard"
```

---

### Task 6: Frontend — clearer filter bar (date + today)

**Files:** `frontend/src/features/appointments/components/AppointmentsFilters.vue`, `.../composables/useAppointmentsPage.ts`, `.../pages/AppointmentsPage.vue`, `.../types` (query params type if needed).

- [ ] **Step 1: Composable date filter.** In `useAppointmentsPage.ts` add a `dateFilter` ref (`const dateFilter = ref('')`). In `fetchAppointments`, after the `q`/`status` params, add: `if (dateFilter.value) params.date = dateFilter.value`. Add a `setToday` helper: `const setToday = () => { dateFilter.value = toLocalDateString(new Date()); return fetchAppointments() }`. In the reset handler, also clear `dateFilter.value = ''`. Export `dateFilter` and `setToday` from the composable's return (and ensure `AppointmentQueryParams` type includes optional `date: string`).

- [ ] **Step 2: Filters UI.** In `AppointmentsFilters.vue` add a `date: string` prop + `'update:date': [value: string]` emit, and a `'today': []` emit. Add between the status select and the Search button:
```vue
<ElDatePicker
  :model-value="date"
  type="date"
  value-format="YYYY-MM-DD"
  :placeholder="t('appointments.dateFilter')"
  style="width: 160px;"
  @update:model-value="(value) => emit('update:date', value || '')"
/>
<ElButton @click="emit('today')">{{ t('appointments.todayFilter') }}</ElButton>
```
Update the Reset disabled condition to `!search && status === 'all' && !date`.

- [ ] **Step 3: Wire in the page.** In `AppointmentsPage.vue` pass `:date="dateFilter"` `@update:date="dateFilter = $event"` `@today="setToday"` to `<AppointmentsFilters>` (bind to the composable's `dateFilter`/`setToday`). The existing reset handler already calls the composable reset (which now clears date).

- [ ] **Step 4: Verify + commit.** `npx vue-tsc -b --noEmit` clean; `npx vitest run` green.
```bash
git add frontend/src/features/appointments
git commit -m "feat(appointments): date filter + Today quick filter"
```

---

### Task 7: Frontend — appointment detail drawer

**Files:** Create `frontend/src/features/appointments/components/AppointmentDetailDrawer.vue`; modify `.../components/AppointmentsTableCard.vue`, `.../pages/AppointmentsPage.vue`, `.../types` (add contact fields to the appointment item type).

- [ ] **Step 1: Extend the item type.** In `features/appointments/types`, add `patient_phone?: string; patient_email?: string; doctor_phone?: string; doctor_email?: string` to the `AppointmentItem` interface.

- [ ] **Step 2: Create `AppointmentDetailDrawer.vue`:**
```vue
<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import type { AppointmentItem } from '../types'

defineProps<{ modelValue: boolean; appointment: AppointmentItem | null }>()
const emit = defineEmits<{ 'update:modelValue': [v: boolean] }>()
const { t } = useI18n()
const dash = (v?: string) => (v && v.trim() ? v : t('appointments.notProvided'))
</script>

<template>
  <el-drawer :model-value="modelValue" :title="t('appointments.detailTitle')" size="420px"
    @update:model-value="(v) => emit('update:modelValue', v)">
    <div v-if="appointment" class="detail">
      <div class="detail-head"><StatusBadge :status="appointment.status" /></div>
      <section class="detail-card">
        <h4>{{ t('appointments.sectionPatient') }}</h4>
        <p class="name">{{ appointment.patient_name }}</p>
        <p>{{ t('appointments.contactPhone') }}: {{ dash(appointment.patient_phone) }}</p>
        <p>{{ t('appointments.contactEmail') }}: {{ dash(appointment.patient_email) }}</p>
      </section>
      <section class="detail-card">
        <h4>{{ t('appointments.sectionDoctor') }}</h4>
        <p class="name">{{ appointment.doctor_name }}</p>
        <p>{{ t('appointments.contactPhone') }}: {{ dash(appointment.doctor_phone) }}</p>
        <p>{{ t('appointments.contactEmail') }}: {{ dash(appointment.doctor_email) }}</p>
      </section>
      <section class="detail-row">
        <div><span class="label">{{ t('appointments.fieldDateTime') }}</span>{{ appointment.appointment_date }} · {{ appointment.appointment_time.slice(0,5) }}</div>
        <div><span class="label">{{ t('appointments.reason') }}</span>{{ dash(appointment.reason) }}</div>
      </section>
      <section v-if="appointment.status === 'completed'" class="detail-card">
        <p><span class="label">{{ t('appointments.diagnosisResult') }}</span>{{ dash(appointment.diagnosis_result) }}</p>
        <p><span class="label">{{ t('appointments.treatmentPlan') }}</span>{{ dash(appointment.treatment_plan) }}</p>
        <p><span class="label">{{ t('appointments.medicalAdvice') }}</span>{{ dash(appointment.medical_advice) }}</p>
      </section>
    </div>
  </el-drawer>
</template>

<style scoped>
.detail { display: flex; flex-direction: column; gap: 12px; }
.detail-card { background: var(--surface-alt); border: 1px solid var(--line); border-radius: var(--radius-card, 12px); padding: 12px; }
.detail-card h4 { margin: 0 0 6px; font-size: 13px; color: var(--muted); }
.detail-card p, .detail-row div { font-size: 13px; color: var(--ink); margin: 2px 0; }
.detail-row { display: flex; gap: 18px; }
.name { font-weight: 600; }
.label { display: block; font-size: 12px; color: var(--muted); }
</style>
```
(Confirm `AppointmentItem` field names — `diagnosis_result`, `treatment_plan`, `medical_advice`, `appointment_date`, `appointment_time`, `patient_name`, `doctor_name`, `reason`, `status` — match the type; adjust if the type uses different names.)

- [ ] **Step 3: Open from the table.** In `AppointmentsTableCard.vue` add a "详情" action button (always visible, for all roles) in the Actions column that emits `detail` with the row: `<ElButton link size="small" @click="emit('detail', row)">{{ t('appointments.viewDetail') }}</ElButton>`; add `detail: [row: AppointmentItem]` to its emits. In `AppointmentsPage.vue`, add `const detailVisible = ref(false)` and `const detailRow = ref<AppointmentItem | null>(null)`, handle `@detail="(row) => { detailRow = row; detailVisible = true }"`, and render `<AppointmentDetailDrawer v-model="detailVisible" :appointment="detailRow" />`.

- [ ] **Step 4: Verify + commit.** `npx vue-tsc -b --noEmit` clean; `npx vitest run` green.
```bash
git add frontend/src/features/appointments
git commit -m "feat(appointments): appointment detail drawer with contact info"
```

---

### Task 8: Verification

- [ ] **Step 1: Backend** — `cd backend && .venv/bin/python -m pytest -q` all green.
- [ ] **Step 2: Frontend** — `cd frontend && npx vue-tsc -b --noEmit` clean; `npx vitest run` green.
- [ ] **Step 3: Playwright** (dev server; seed run so `ops_test` exists). Both locales:
  - **operator** (`ops_test`/`Demo@12345`): nav = 工作台/预约管理/个人中心; dashboard has no Quick Actions; appointments has NO `+ 新建预约` and NO row action buttons; the **详情** drawer opens and shows patient/doctor phone+email; filter bar has name/status/date/Today and filters work; status pills read 待就诊/诊疗中.
  - **doctor/admin**: detail drawer shows contact info; action buttons still present; statuses relabeled.
  - **patient**: (own appts) detail drawer shows contact blank (—/未填写). 0 missing i18n keys.
- [ ] **Step 4: Commit any fixups.**

---

## Notes for the executor
- The only migration is the `users` `role` choices `AlterField` (non-destructive).
- Keep English `status.pending` = "Pending" (only `confirmed` → "Consulting") so existing StatusBadge text test stays green.
- After merge, deploy via `service-update` from a fresh `main` worktree, then re-run the demo seed on the server so `ops_test` exists (run `seed_demo_full.py` in the backend container like before).
