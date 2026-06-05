# Visual Design System ("Calm Clinical") — Design

Date: 2026-06-04
Status: Approved (design), pending implementation

## Context

Sub-project 2 of 3 in the overall design optimization (after the role-based
IA redesign; sub-project 3 = key-flow polish, later). The app's visuals grew
ad-hoc: status colors are hard-coded differently across the dashboard donut,
appointment tags, doctor-profile badges, etc.; button/table/card styling
varies per page. Goal: one consistent, professional **Calm Clinical** system
applied across the app via central design tokens + standardized components.

Presentation-only: no behavior, data, API, or DB changes. English i18n
values that existing tests assert on must stay byte-identical.

## Direction (chosen)

**A · Calm Clinical** — refine the existing blue-indigo identity: soft
neutrals, generous whitespace, light shadows, 12px card radius. Comfortable
table density.

## Design tokens (CSS custom properties)

Define once (central `src/styles/tokens.css`, imported by `style.css`) and use
everywhere via `var(--…)`.

```
/* brand */
--brand-primary:#3B5BDB; --brand-primary-hover:#3250C4; --brand-primary-soft:#EEF2FB;
/* text & lines */
--ink:#1E295A;            /* headings */
--text:#3A4256;           /* body */
--muted:#707A8C;          /* secondary */
--line:#E2E6F0;           /* borders */
--line-soft:#F3F5F9;      /* row separators */
/* surfaces */
--surface:#FFFFFF; --surface-alt:#FAFBFD; --page-bg:#EEF2F7;
/* status (bg / fg pairs) */
--status-pending-bg:#FFF5E6;   --status-pending-fg:#B9821A;   /* warning */
--status-confirmed-bg:#E8EEFC; --status-confirmed-fg:#2D63C8; /* info */
--status-completed-bg:#E7F6EC; --status-completed-fg:#2E7D4F; /* success */
--status-cancelled-bg:#FBE9EC; --status-cancelled-fg:#C2334A; /* danger */
--status-neutral-bg:#EEF0F4;   --status-neutral-fg:#707A8C;   /* draft/none */
/* radius / shadow / spacing */
--radius-card:12px; --radius-control:10px; --radius-pill:999px;
--shadow-card:0 6px 16px rgba(36,60,120,.06);
--space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px; --space-5:20px; --space-6:24px;
```

Map Element Plus theme to brand via its CSS vars at `:root` (so EP buttons,
focus rings, links inherit): `--el-color-primary` and its light/dark
derivatives = the brand scale; `--el-border-radius-base` = 10px.

Typography: page title 24px/700 `--ink`; section heading 16px/600; body 14px;
small 12–13px `--muted`. Keep the existing system + `PingFang SC` CJK stack.

## Component conventions

- **Buttons:** primary = solid `--brand-primary` (hover `--brand-primary-hover`);
  secondary = white + `--brand-primary` text/1px border; danger = white +
  danger text/border; **row actions = small pill** (radius-pill) in the
  semantic color (confirm=primary, complete=success, cancel=danger) — already
  done in the appointments table (Task: generalize the pattern); tertiary =
  text/link.
- **Status tags (unify):** one shared **`StatusBadge`** component
  (`src/shared/components/StatusBadge.vue`) that takes a status key and a kind
  (`appointment` | `publish`) and renders a pill using the status tokens. A
  single map: appointment `pending/confirmed/completed/cancelled` →
  pending/confirmed/completed/neutral-cancelled tokens; publish
  `published→completed(green)`, `pendingReview→pending`, `draft→neutral`,
  `rejected→cancelled`, `none→neutral`, `approved→completed`. Replace the
  ad-hoc tag styling in: Dashboard (legend + donut colors), AppointmentsTable,
  DoctorsPage list, DoctorDetailPage header (it currently uses
  `PublishStatusBadge` — fold/align that into `StatusBadge` or restyle it to
  tokens; **keep its English text** so its test passes), PatientHomePage,
  RecordsPage. The Dashboard donut `conic-gradient` should use the four status
  `--status-*-fg` tokens.
- **Tables:** comfortable density (row padding `14px 16px`, ~52px), header in
  `--surface-alt` with `--muted` 12px labels, 1px `--line-soft` row
  separators, hover highlight (`--brand-primary-soft`), subtle zebra (even
  rows `--surface-alt`), wrapped in a `--radius-card` card with `--shadow-card`.
- **Cards / panels:** white, `--radius-card`, 1px `--line`, `--shadow-card`.
  Emphasis/value cards use `--brand-primary-soft` bg + `--brand-primary` label.
- **Page header:** title (`--ink` 24/700) + subtitle (`--muted` 13), consistent
  spacing — standardize the `.page` header block used across views.
- **Forms:** inputs `--radius-control`, `#F8FBFF` bg, `--line`-ish border,
  brand focus ring; labels 12–13px/600 `--text` (the login form already does
  this — promote to the shared pattern).

## File structure

- `src/styles/tokens.css` *(new)* — the CSS custom properties above.
- `src/styles/components.css` *(new, or fold into `style.css`)* — shared
  utility/component classes: `.page`, `.page-header`, `.card`, `.value-card`,
  table helpers, button helpers built on tokens.
- `src/style.css` — import tokens/components; set EP `--el-color-primary` etc.
- `src/shared/components/StatusBadge.vue` *(new)* — unified status pill.
- Page sweep (restyle to tokens/StatusBadge, no logic change): `App.vue`
  (shell already close — align to tokens), `views/DashboardPage.vue`,
  `features/appointments/components/AppointmentsTableCard.vue` +
  filters/dialogs, `views/DoctorsPage.vue`,
  `features/content/pages/admin/DoctorDetailPage.vue`, `views/RecordsPage.vue`,
  `views/PatientsPage.vue`, `views/TimeSlotsPage.vue`, `views/ProfilePage.vue`,
  `views/PatientHomePage.vue`, portal pages, `PublishStatusBadge.vue`.

Keep changes scoped to styling + the StatusBadge swap. Don't restructure logic.

## Testing

- `vue-tsc -b --noEmit` clean; `vitest run` green (PublishStatusBadge /
  carousel text assertions unchanged).
- Playwright before/after screenshots per role + both locales; visual check
  that status colors, buttons, tables, cards are consistent and no contrast
  regressions.

## Out of scope

- Sub-project 3 (key-flow polish). No new features; no dark mode.
