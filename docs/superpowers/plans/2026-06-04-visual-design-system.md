# Visual Design System ("Calm Clinical") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply one consistent "Calm Clinical" visual system across the app via centralized design tokens, a unified status badge, and standardized table/card/button conventions.

**Architecture:** Presentation-only. `src/style.css` already has a `:root` token block that components reference — **re-point those token values** (highest-leverage, restyles app-wide) rather than adding a parallel file; add a few missing tokens; theme Element Plus via its CSS vars; unify all status pills into one `StatusBadge` component driven by the tokens. No behavior/data/API/DB changes.

**Tech Stack:** Vue 3 `<script setup>`, Element Plus, vue-i18n, vitest. CSS custom properties.

Spec: `docs/superpowers/specs/2026-06-04-visual-design-system-design.md`

> **Note on the spec:** the spec proposed a new `tokens.css`; during planning we found `style.css` already centralizes tokens in `:root`, so we evolve those in place (DRY, follows existing pattern). Same outcome.

---

## File structure
- `src/style.css` — re-point + extend `:root` tokens; add Element Plus theme vars; add shared `.status-pill` + table/card helper classes.
- `src/shared/components/StatusBadge.vue` *(new)* — unified status pill (appointment + publish kinds).
- `src/shared/components/__tests__/StatusBadge.spec.ts` *(new)* — unit test.
- Status surfaces adopting `StatusBadge` / tokens: `features/appointments/components/AppointmentsTableCard.vue` (+ parent `pages/AppointmentsPage.vue` drops the `statusTagType` prop), `views/DashboardPage.vue` (legend + donut), `views/DoctorsPage.vue`, `features/content/pages/admin/DoctorDetailPage.vue` + `features/content/components/PublishStatusBadge.vue`, `views/PatientHomePage.vue`, `views/RecordsPage.vue`.

---

### Task 1: Re-point + extend design tokens; theme Element Plus

**Files:** Modify `src/style.css` (the `:root` block at the top, lines ~1–31).

- [ ] **Step 1: Replace the `:root` token values** with the Calm Clinical palette and add the new tokens. Replace the existing `:root { … }` opening block's variables with:

```css
:root {
  --bg: #eef2f7;
  --page-bg: #eef2f7;
  --card: #ffffff;
  --surface-alt: #fafbfd;
  --line: #e2e6f0;
  --line-soft: #f3f5f9;
  --ink: #1e295a;
  --text: #1e295a;
  --muted: #707a8c;
  --primary: #3b5bdb;
  --primary-a: #3b5bdb;
  --primary-b: #3250c4;
  --primary-soft: #eef2fb;
  --success-bg: #e7f6ec;  --success-text: #2e7d4f;
  --warn-bg: #fff5e6;     --warn-text: #b9821a;
  --danger-bg: #fbe9ec;   --danger-text: #c2334a;
  --status-total-bg: #edf2f7;     --status-total-text: #2d3748;
  --status-pending-bg: #fff5e6;   --status-pending-text: #b9821a;
  --status-confirmed-bg: #e8eefc; --status-confirmed-text: #2d63c8;
  --status-completed-bg: #e7f6ec; --status-completed-text: #2e7d4f;
  --status-cancelled-bg: #fbe9ec; --status-cancelled-text: #c2334a;
  --status-neutral-bg: #eef0f4;   --status-neutral-text: #707a8c;
  --action-unavailable-bg: #fff5e6;  --action-unavailable-border: #f0d49b;  --action-unavailable-text: #b9821a;
  --action-available-bg: #e8eefc;    --action-available-border: #c2d2f5;    --action-available-text: #2d63c8;
  --action-clear-bg: #f8fafd;        --action-clear-border: #cfd7e6;        --action-clear-text: #4a5568;
  --radius-card: 12px;
  --radius-control: 10px;
  --radius-pill: 999px;
  --shadow-card: 0 6px 16px rgba(36, 60, 120, 0.06);
}
```

(Keep any other declarations that were inside `:root` below these if present; only the variables above are being set/added.)

- [ ] **Step 2: Theme Element Plus** — append to `src/style.css` (after the `:root` block) so EP primary/links/focus inherit the brand:

```css
:root {
  --el-color-primary: #3b5bdb;
  --el-color-primary-light-3: #6b86e6;
  --el-color-primary-light-5: #9db0ee;
  --el-color-primary-light-7: #cdd7f7;
  --el-color-primary-light-8: #e1e8fb;
  --el-color-primary-light-9: #eef2fb;
  --el-color-primary-dark-2: #3250c4;
  --el-border-radius-base: 10px;
}
```

- [ ] **Step 3: Verify build + visual smoke** — Run `cd frontend && npx vue-tsc -b --noEmit` (expect clean) and `npx vitest run` (expect green). Start the dev server and screenshot the dashboard + appointments to confirm the palette shifted with no broken contrast.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/style.css
git commit -m "feat(ui): re-point design tokens to Calm Clinical palette + theme Element Plus"
```

---

### Task 2: Unified StatusBadge + adopt across status surfaces

**Files:** Create `src/shared/components/StatusBadge.vue`, `src/shared/components/__tests__/StatusBadge.spec.ts`; modify `src/style.css` (add `.status-pill`); modify the status surfaces listed below.

- [ ] **Step 1: Add the shared pill style** to `src/style.css`:

```css
.status-pill {
  display: inline-flex; align-items: center;
  font-size: 12px; font-weight: 600;
  padding: 2px 11px; border-radius: var(--radius-pill);
  white-space: nowrap;
}
.status-pill[data-variant='pending']   { background: var(--status-pending-bg);   color: var(--status-pending-text); }
.status-pill[data-variant='confirmed'] { background: var(--status-confirmed-bg); color: var(--status-confirmed-text); }
.status-pill[data-variant='completed'] { background: var(--status-completed-bg); color: var(--status-completed-text); }
.status-pill[data-variant='cancelled'] { background: var(--status-cancelled-bg); color: var(--status-cancelled-text); }
.status-pill[data-variant='neutral']   { background: var(--status-neutral-bg);   color: var(--status-neutral-text); }
```

- [ ] **Step 2: Write the failing test** `src/shared/components/__tests__/StatusBadge.spec.ts`:

```ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import StatusBadge from '../StatusBadge.vue'

describe('StatusBadge', () => {
  it('renders the translated appointment status and maps variant', () => {
    const w = mount(StatusBadge, { props: { kind: 'appointment', status: 'pending' } })
    expect(w.attributes('data-variant')).toBe('pending')
    expect(w.text()).toContain('Pending')
  })
  it('maps cancelled appointment to the cancelled variant', () => {
    const w = mount(StatusBadge, { props: { kind: 'appointment', status: 'cancelled' } })
    expect(w.attributes('data-variant')).toBe('cancelled')
  })
  it('maps publish statuses to variants', () => {
    expect(mount(StatusBadge, { props: { kind: 'publish', status: 'published' } }).attributes('data-variant')).toBe('completed')
    expect(mount(StatusBadge, { props: { kind: 'publish', status: 'pending' } }).attributes('data-variant')).toBe('pending')
    expect(mount(StatusBadge, { props: { kind: 'publish', status: 'rejected' } }).attributes('data-variant')).toBe('cancelled')
    expect(mount(StatusBadge, { props: { kind: 'publish', status: 'draft' } }).attributes('data-variant')).toBe('neutral')
  })
})
```

Run: `cd frontend && npx vitest run src/shared/components/__tests__/StatusBadge.spec.ts` → FAIL (component missing).

- [ ] **Step 3: Implement** `src/shared/components/StatusBadge.vue`:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

type Kind = 'appointment' | 'publish'
const props = defineProps<{ kind: Kind; status: string }>()
const { t } = useI18n()

const APPT_VARIANT: Record<string, string> = {
  pending: 'pending', confirmed: 'confirmed', completed: 'completed', cancelled: 'cancelled',
}
const PUBLISH_VARIANT: Record<string, string> = {
  published: 'completed', approved: 'completed', pending: 'pending',
  pendingReview: 'pending', rejected: 'cancelled', draft: 'neutral', none: 'neutral',
}
const PUBLISH_LABEL_KEY: Record<string, string> = {
  published: 'publishStatus.published', approved: 'publishStatus.approved',
  pending: 'publishStatus.pendingReview', pendingReview: 'publishStatus.pendingReview',
  rejected: 'publishStatus.rejected', draft: 'publishStatus.draft', none: 'publishStatus.draft',
}

const variant = computed(() =>
  props.kind === 'appointment'
    ? APPT_VARIANT[props.status] ?? 'neutral'
    : PUBLISH_VARIANT[props.status] ?? 'neutral',
)
const label = computed(() =>
  props.kind === 'appointment'
    ? t(`status.${props.status}`)
    : t(PUBLISH_LABEL_KEY[props.status] ?? 'publishStatus.draft'),
)
</script>

<template>
  <span class="status-pill" :data-variant="variant">{{ label }}</span>
</template>
```

Run the test again → PASS. (`status.*` and `publishStatus.*` keys already exist in the locales.)

- [ ] **Step 4: Adopt in the appointments table.** In `AppointmentsTableCard.vue`, replace the status `<ElTag :type="statusTagType(row.status)" size="small">{{ t('status.' + row.status) }}</ElTag>` with `<StatusBadge kind="appointment" :status="row.status" />` (import StatusBadge). Remove the now-unused `statusTagType` prop from the component's `defineProps`, and in the parent `features/appointments/pages/AppointmentsPage.vue` remove the `:status-tag-type`/`statusTagType` it passes down (and the `statusTagType` helper if now unused). Run `vitest run` (the existing appointments test must stay green — it doesn't assert the tag type).

- [ ] **Step 5: Adopt elsewhere.** Replace ad-hoc status tags with `<StatusBadge .../>`:
  - `views/DoctorsPage.vue` — profile-status column → `<StatusBadge kind="publish" :status="row.status" />` (the row status keys already are published/pending/draft/rejected/none — confirm and map; the `none` shows as draft label, acceptable, OR add a `publishStatus.none`='Not created' label — keep existing `doctorStatus.*` if the page uses those; if so leave DoctorsPage as-is and only restyle its tag to `.status-pill`). Prefer minimal: if DoctorsPage uses `doctorStatus.*`, just swap its `el-tag` for a `<span class="status-pill" :data-variant="…">` mapping, keeping its labels.
  - `views/RecordsPage.vue` and `views/PatientHomePage.vue` — appointment status tags → `<StatusBadge kind="appointment" :status="…" />`.
  - `views/DashboardPage.vue` — the legend swatch colors and the donut `conic-gradient` currently use hard-coded hex (`#ed8936` etc.); change them to the status text tokens (`var(--status-pending-text)`, `--status-confirmed-text`, `--status-completed-text`, `--status-cancelled-text`). The "Today Schedule" status tags → `<StatusBadge kind="appointment" .../>`.
  - `features/content/components/PublishStatusBadge.vue` — replace its scoped hard-coded colors with the shared `.status-pill[data-variant]` (map its existing variants `published/pending/rejected/draft` to `completed/pending/cancelled/neutral`). **Keep its label text unchanged** (`PublishStatusBadge.spec.ts` asserts 'Published'/'Pending review'). Used by `DoctorDetailPage.vue` header.

- [ ] **Step 6: Verify + commit**

Run `cd frontend && npx vue-tsc -b --noEmit` (clean) and `npx vitest run` (green, incl. StatusBadge + PublishStatusBadge + appointments tests).

```bash
git add -A
git commit -m "feat(ui): unified StatusBadge driven by design tokens; adopt across status surfaces"
```

---

### Task 3: Table / card / page-header / button conventions

**Files:** Modify `src/style.css` (add shared helper classes); apply to `views/DashboardPage.vue`, `AppointmentsTableCard.vue`, `views/DoctorsPage.vue`, `views/RecordsPage.vue`, `views/PatientsPage.vue`, `features/content/pages/admin/DoctorDetailPage.vue`, `views/ProfilePage.vue`, `views/PatientHomePage.vue`.

- [ ] **Step 1: Add shared helper classes** to `src/style.css`:

```css
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--ink); margin: 0; }
.page-header p { font-size: 13px; color: var(--muted); margin: 4px 0 0; }
.surface-card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius-card); box-shadow: var(--shadow-card); }
.value-card { background: var(--primary-soft); border: 1px solid #dde6fa; border-radius: var(--radius-card); }
/* comfortable Element Plus tables, app-wide */
.el-table { --el-table-border-color: var(--line-soft); --el-table-row-hover-bg-color: var(--primary-soft); }
.el-table th.el-table__cell { background: var(--surface-alt); color: var(--muted); font-weight: 600; }
.el-table .el-table__cell { padding: 11px 0; }
.el-table .el-table__row--striped td.el-table__cell { background: var(--surface-alt); }
```

- [ ] **Step 2: Standardize page headers** — in each listed view, ensure the title/subtitle block uses `class="page-header"` with `<h2>` + `<p>` (most already render an `h2` + `p`; wrap/add the class so spacing + `--ink`/`--muted` are consistent). Concrete: replace the existing hero/title `<div>`/`<section>` wrapper around the page `<h2>`+`<p>` with `<div class="page-header">…</div>`. No text changes.

- [ ] **Step 3: Tables comfortable + striped** — for the Element Plus `<el-table>` instances (appointments, doctors, records, patients), add the `stripe` prop and rely on the global `.el-table` overrides from Step 1 for header/hover/separators. For the hand-rolled grid table in `AppointmentsTableCard` (if it is `el-table`, this is automatic; if it's a CSS grid, apply matching row padding/hover via its scoped styles using the tokens). Keep row-action **pill** buttons (already in place) consistent.

- [ ] **Step 4: Cards & value cards** — swap bespoke card/panel wrappers to `class="surface-card"` and emphasis/stat tiles to `class="value-card"` where they match (dashboard stat tiles, profile panels, patient-home cards). Visual only.

- [ ] **Step 5: Verify + commit**

Run `cd frontend && npx vue-tsc -b --noEmit` (clean), `npx vitest run` (green).

```bash
git add -A
git commit -m "feat(ui): consistent page headers, comfortable tables, card conventions"
```

---

### Task 4: Verification

- [ ] **Step 1: Typecheck + tests** — `cd frontend && npx vue-tsc -b --noEmit` (clean); `npx vitest run` (all green incl. StatusBadge/PublishStatusBadge/carousel/appointments).
- [ ] **Step 2: Playwright visual sweep** — for each role (admin, doctor, patient) in both locales, screenshot dashboard, appointments, doctors list + detail, records, patient home. Confirm: consistent status pill colors everywhere, brand-blue primary buttons, comfortable striped tables, consistent page headers/cards; no contrast or layout regressions; **0 missing i18n keys** in console.
- [ ] **Step 3: Commit any fixups.**

---

## Notes for the executor
- Purely visual. If a page already uses the `:root` tokens, Task 1 restyles it for free — don't rewrite such pages, just confirm. Only convert **hard-coded** colors to tokens.
- Keep all English i18n text identical (PublishStatusBadge / carousel tests assert text).
- Don't change component logic, props' data flow, or layouts beyond styling. If a "swap to StatusBadge" would change rendered text, stop and reconcile keys instead.
- After merge, publish to the demo via the standard `service-update` from a fresh `main` worktree.
